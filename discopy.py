#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright 2015 Fabian Grimme

This file is part of DiscoPy.

DiscoPy is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any late
version.
DiscoPy is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
DiscoPy. If not, see <http://www.gnu.org/licenses/>.
"""

import re
import os
import sys
import json
import logging
from time import time, sleep
import traceback
from PyQt4 import QtGui, QtCore
from dialog import Ui_MainWindow
from namebuilder import NameBuilder
from tagdata import TagData
from imageloader import ImageHandler
from discogs_client import Client
from os.path import expanduser
import urllib2

try:
    from auth import CONSUMER_KEY, CONSUMER_SECRET, TOKEN, SECRET
except:
    print 'Discogs OAuth credentials are missing!'

# sys.setdefaultencoding('utf-8')

CHCK_NTWRK = 'http://www.google.com'
PRGRSS_ICN = 'progress.gif'
ICN_DIR = 'icons'
SPLSH_SCRN = 'discopy_800px.png'
THMB_DIR = 'thumbs'
TMP_IMG_DIR = 'images'
STNGS = 'settings'
SNTX_STNGS = 'syntax.json'
RLS_SNTX = "artist - release [labels year]"
TRCK_SNTX = "index track"


def resource_path(relative):
    return os.path.join(getattr(sys, '_MEIPASS',
        os.path.abspath(".")), relative)
cert_path = resource_path('cacert.pem')

# Set `REQUESTS_CA_BUNDLE` path for `requests` module pem
# file if not in development mode.
if os.path.exists(cert_path):
    os.environ['REQUESTS_CA_BUNDLE'] = cert_path


class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    data_ready = QtCore.pyqtSignal(object)

    def __init__(self, function, *args, **kwargs):
        super(Worker, self).__init__()
        self._logger = logging.getLogger('discopy.main')
        self._logger.debug('create worker')
        self._function = function
        self._args = args
        self._kwargs = kwargs

    @QtCore.pyqtSlot()
    def run(self):
        self._logger.debug('call ' + self._function.__name__)
        data = self._function(*self._args, **self._kwargs)
        self._logger.debug('finished ' + self._function.__name__)
        self._logger.debug('thread id of worker: ' +
            str(QtCore.QThread.currentThreadId()))
        self.data_ready.emit(data)
        self.finished.emit()


class DiscoPy(QtGui.QMainWindow):

    def __init__(self, ui, client, name_builder, tagdata,
            image_handler, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self._ui = ui
        self._ui.setupUi(self)
        self._name_builder = name_builder
        # Discogs api client
        self._client = client
        self._tagger = tagdata
        self._image_handler = image_handler
        self._query = ""
        self._query_type = ""
        # Discogs api response obejects
        self._discogs_data = []
        self._discogs_data_index = 0
        # Simple model for the parsed discogs data.
        self._parsed_data = {}
        self._parsed_data_id = 0
        self._img_download_pathes = {}
        # Index for the thumb preview of artwork images.
        self._thumb_index = 0
        # Index counter to convert alpha numeric track 
        # indices to numeric indices.
        self._track_index = 1
        # Animation to show download progress
        self._progress = None
        # Keep references to worker threads while threads are running
        self._thread_pool = []
        # Refereances to worker objects
        self._worker_pool = []
        # Timer to ensure worker threads are started just once per second.
        self._worker_start = 0
        # logging
        self._logger = logging.getLogger('discopy.main')
        # Signals
        self._ui.btn_imgs.clicked.connect(self._get_images)
        self._ui.btn_srch.clicked.connect(self._search)
        self._ui.btn_prv.clicked.connect(lambda: self._skip(-1))
        self._ui.btn_nxt.clicked.connect(lambda: self._skip(1))
        self._ui.btn_rnm.clicked.connect(self._rename)
        self._ui.btn_tgs.clicked.connect(self._set_tags)
        self._ui.lndt_t_sntx.text_modified.connect(self._update_list)
        self._ui.lndt_f_sntx.text_modified.connect(self._update_list)
        self._ui.lndt_t_sntx.text_modified.connect(self._save_syntax)
        self._ui.lndt_f_sntx.text_modified.connect(self._save_syntax)
        self._ui.lndt_t_sntx.returnPressed.connect(self._update_list)
        self._ui.lndt_f_sntx.returnPressed.connect(self._update_list)
        self._ui.lndt_url.query.connect(self._set_query)
        self._ui.lndt_rls.query.connect(self._set_query)
        self._ui.lndt_brcde.query.connect(self._set_query)
        self._ui.lndt_url.focus.connect(self._set_focus)
        self._ui.lndt_rls.focus.connect(self._set_focus)
        self._ui.lndt_brcde.focus.connect(self._set_focus)
        self._ui.lst_ld.drop_finished.connect(self._init_drop_search)
        self.connect(self._ui.lbl_cvr, QtCore.SIGNAL('clicked'),
            self._get_thumb)
        # Init
        self._set_focus()
        # Initialize the progress animation
        imagepath = os.path.abspath(os.path.join(os.path.dirname(__file__),
            'icons', PRGRSS_ICN))
        self._progress = QtGui.QMovie(imagepath, QtCore.QByteArray(), self)
        self._progress.setCacheMode(QtGui.QMovie.CacheAll)
        self._progress.setSpeed(100)
        self._ui.lbl_prgrss.setMovie(self._progress)
        # Initialize the syntax line edits.
        self._set_syntax()

    def _init_drop_search(self):
        release_title = self._get_tags()
        if release_title:
            self._query = release_title
            self._query_type = 'release'
            self._ui.lndt_rls.setText(release_title)
            self._search()

    def center(self):
        """Center the mainwindow when it is started.
        """
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _skip(self, step):
        """Skip forward or backward in the search results.
        """
        if len(self._discogs_data) >= 1:
            self._discogs_data_index = (self._discogs_data_index + step) % \
                (len(self._discogs_data))
            self._logger.debug('skip results - step: %d - index: %d' %
                (step, self._discogs_data_index))
            # Disable the search buttons during search process.
            self._toggle_search_buttons()
            # Skip and parse the search results in a worker thread.
            # Show data when the ´data_ready´ signal is emitted.
            self._run_worker(self._show_data, self._parse_data)

    def _search(self):
        """Move the search to a worker thread. Show data in the list widget
           when the request returns.
        """
        if not self._query:
            return
        self._logger.debug('search for: ' + self._query)
        # Disable the search buttons during search process.
        self._toggle_search_buttons()
        # Run the search in a worker thread. Show search results when
        # the ´data_ready´ signal is emitted.
        self._run_worker(self._show_data, self._get_data)

    def _get_data(self):
        """Send a discogs api request according to the request type. The
           request type is defined by the search query provided by the
           user input.
        """
        self._logger.debug('get data')
        self._discogs_data, self._discogs_data_index = [], 0
        try:
            if self._query_type == 'url':
                type_, id_ = self._parse_url(self._query)
                # Search for a master release by id.
                if type_ == 'master':
                    self._logger.debug('get master by id: ' + self._query)
                    self._discogs_data.append(self._client.master(int(id_)))
                # Search for a release by id.
                elif type_ == 'release':
                    self._logger.debug('get release by id: ' + self._query)
                    self._discogs_data.append(self._client.release(int(id_)))
            # Search for a release by name.
            elif self._query_type == 'release':
                self._logger.debug('search release by name: ' + self._query)
                self._discogs_data = self._client.search(self._query,
                    type='release')
            # Search for a release by barcode.
            elif self._query_type == 'barcode':
                self._logger.debug('get release by barcode: ' + self._query)
                self._discogs_data = self._client.search(barcode=self._query)

            # Parse the data returned by discogs api.
            if len(self._discogs_data):
                self._parse_data()

        except Exception:
            self._logger.error(traceback.format_exc())

    def _parse_data(self):
        """Parse the discogs response to a simple data object. Since the
           discgos client uses lazy instatiation this is needed to move all
           api requests to one worker thread.
        """
        # Get data from the discogs seach results for the current page
        # specified by ´self._discogs_data_index´.
        discogs_data = self._discogs_data[self._discogs_data_index]

        # Set id of the currently displayed release.
        self._parsed_data_id = discogs_data.id

        self._logger.debug('parse data for release id: %s' %
            (str(self._parsed_data_id)))

        # Reset the thumb index for artwork preview.
        self._thumb_index = 0

        # Check if the release is has already been parsed.
        if self._parsed_data_id in self._parsed_data.keys():
            return
        else:
            self._parsed_data[self._parsed_data_id] = {
                'tracks': {},
                'release': {}}

        # Get the syntax to build the release and track names.
        t_syntax = unicode(self._ui.lndt_t_sntx.text())
        d_syntax = unicode(self._ui.lndt_f_sntx.text())

        # Parse discogs_data.
        release_data = {}
        release_data['title'] = getattr(discogs_data, 'title') or 'Unknown' \
            if hasattr(discogs_data, 'title') else 'Unknown'

        release_data['year'] = str(getattr(discogs_data, 'year') or 'Unknown') \
            if hasattr(discogs_data, 'year') else 'Unknown'

        release_data['country'] = getattr(discogs_data, 'country') or \
            'Unknown' if hasattr(discogs_data, 'country') else 'Unknown'

        release_data['genres'] = ' ,'.join(genre for genre in
            getattr(discogs_data, 'genres') or ['Unknown']) \
            if hasattr(discogs_data, 'genres') else 'Unknown'

        # release_data['artist'] = getattr(discogs_data.artists[0],
        # 'name') or 'Unknown' if hasattr(discogs_data, 'artists')
        # else 'Unknown'

        release_data['artist'] = ' ,'.join(getattr(artist, 'name')
            for artist in getattr(discogs_data, 'artists')
            or ['Unknown']) if hasattr(discogs_data, 'artists') \
            else 'Unknown'

        # release_data['label'] = getattr(discogs_data.labels[0], 'name')
        # if hasattr(discogs_data, 'labels') else 'Unknown'

        release_data['label'] = ' ,'.join(getattr(label, 'name')
            for label in getattr(discogs_data, 'labels')
            or ['Unknown']) if hasattr(discogs_data, 'labels') \
            else 'Unknown'

        release_data['images'] = getattr(discogs_data, 'images') \
            or [] if hasattr(discogs_data, 'images') else []

        release_data['id'] = getattr(discogs_data, 'id') \
            if hasattr(discogs_data, 'id') else 'Unknown ID'

        # Build release name.
        release_name = self._name_builder.build_name(
            d_syntax, release_data, None)
        release_data['name'] = release_name

        # Store the parsed release data for the current search.
        self._parsed_data[discogs_data.id]['release'] = release_data

        # Parse tracklist data
        if hasattr(discogs_data, 'tracklist'):
            for track in discogs_data.tracklist:
                track_data = {}
                track_data['title'] = track.title \
                    if hasattr(track, 'title') else 'Unknown Title'
                track_data['index'] = str(track.position) \
                    if hasattr(track, 'position') else ''
                # Build track name.
                track_name = self._name_builder.build_name(
                    t_syntax, release_data, track_data)
                track_data['name'] = track_name
                # Store the track data.
                id_ = self._parsed_data_id
                self._parsed_data[id_]['tracks'][track_name] = track_data
        self._logger.debug('parsing finished')

    def _show_data(self):
        """Initialize the search list widget with the parsed data
           from the discogs search results.
        """
        self._logger.debug('show data fior release id: %s' %
            (str(self._parsed_data_id)))

        # Get data for the current release.
        try:
            release_data = self._parsed_data[self._parsed_data_id]
        except Exception:
            self._logger.error(traceback.format_exc())
            # Enable the search buttons.
            self._toggle_search_buttons()
            return

        # Clear list first.
        self._ui.lst_nw.clear()

        # Set list widgets for all tracks in the parsed data.
        for track in release_data['tracks'].values():
            release_data['track'] = track
            self._ui.lst_nw.data_dropped(track['name'], "track",
                meta=release_data, editable=True)

        self._ui.lst_nw.sortItems(QtCore.Qt.AscendingOrder)

        # Set list widget for the release.
        self._ui.lst_nw.data_dropped(release_data['release']['name'],
            "release", meta=release_data, editable=True)

        # Color the list widget background alternatingly.
        self._ui.lst_nw.color_items()

        # Initialize the info labels.
        self._ui.lbl_artst.setText(release_data['release']['artist'])
        self._ui.lbl_rls.setText(release_data['release']['title'])
        self._ui.lbl_lbl.setText(release_data['release']['label'])
        self._ui.lbl_yr.setText(release_data['release']['year'])
        self._ui.lbl_gnr.setText(release_data['release']['genres'])

        # Enable the search buttons.
        self._toggle_search_buttons()

        # Get the artwork preview.
        self._get_thumb()

        self._logger.debug('finished showing data')

    def _parse_url(self, url):
        """Parse the discogs url to determine the release type and
           extract the release id.
        """
        self._logger.debug('parse url: ' + unicode(url))
        search = re.search('(master|release){1}/{1}(\d*)', url, re.UNICODE)
        if search:
            self._logger.debug('type: %s - id: %s' % (search.group(1),
                str(search.group(2))))
            return (search.group(1), search.group(2))
        else:
            self._logger.debug('type: None, id: None')
            return (None, None)

    def _get_thumb(self):
        """Get a thumbnail preview of the artwork.
        """

        try:
            # Get data for the current release.
            release_data = self._parsed_data[self._parsed_data_id]['release']

            self._logger.debug('get thumb for release id: ' +
                str(release_data['id']))
            label = self._ui.lbl_cvr
            uri150 = release_data['images'][self._thumb_index]['uri150']
            imagename = uri150.split('/')[-1]
            imagedir = resource_path(THMB_DIR)
            if not os.path.exists(imagedir):
                os.makedirs(imagedir)
            imagepath = os.path.join(imagedir, imagename)
            # Download preview image in a worker thread if it does not exist.
            if not os.path.isfile(imagepath):
                self._run_worker(lambda: self._show_thumb(label, imagepath),
                    self._image_handler.get_file, imagepath, uri150)
            else:
                self._show_thumb(label, imagepath)

            self.disconnect(self._ui.lbl_cvr, QtCore.SIGNAL('clicked'),
                self._get_thumb)

        except Exception:
            self._logger.error(traceback.format_exc())
        self._logger.debug('finished getting thumbs')

    def _show_thumb(self, label, imagepath):
        """Show the artwork preview in the preview label.
        """
        self._logger.debug('show thumb')

        images = self._parsed_data[self._parsed_data_id]['release'].get(
            'images') or []

        if not os.path.isfile(imagepath):
            return

        if len(images):
            label.setPixmap(QtGui.QPixmap(imagepath))
            self._thumb_index = (self._thumb_index + 1) % len(images)

        self.connect(self._ui.lbl_cvr, QtCore.SIGNAL('clicked'),
            self._get_thumb)

    def _update_list(self):
        """Update the list widget when syntax changes are
           made in the syntax line edit fields.
        """

        self._logger.debug('update list')

        for i in range(self._ui.lst_nw.count()):
            item = self._ui.lst_nw.item(i)

            if not hasattr(item, 'data'):
                continue
            if not hasattr(item, 'type'):
                continue

            # Update the release widget.
            if item.type == "release":
                syntax = unicode(self._ui.lndt_f_sntx.text())
                new_txt = self._name_builder.build_name(syntax, item.data, None)
                item.setText(new_txt.strip())

            if not hasattr(item, 'track'):
                continue
            # Update the track widgets.
            if item.type == "track":
                syntax = unicode(self._ui.lndt_t_sntx.text())
                new_txt = self._name_builder.build_name(syntax,
                    item.data, item.track)
                item.setText(new_txt)
        self._logger.debug('finished updating list')

    def _run_worker(self, slot, function, *args, **kwargs):
        """Provides a g.eneric worker thread.
        @param slot: callback function to be called when the
        function is finished.
        @param function: callable that should be called from
        within the worker thread.
        @param args: argument list passed to ´function´.
        @param kwargs: argument dictionary passed to ´function´.
        """

        self._logger.debug('thread id: ' + str(
            QtCore.QThread.currentThreadId()))
        self._ui.lbl_prgrss.show()
        self._progress.start()
        # No parent!
        thread = QtCore.QThread()
        # Need to keep a reference to the thread while it is running.
        self._thread_pool.append(thread)
        self._logger.debug('threads in pool ' + str(len(self._thread_pool)))
        # No parent!
        worker = Worker(function, *args, **kwargs)
        # Need to keep a reference to the worker while it is living
        # inside the worker thread.
        self._worker_pool.append(worker)
        self._logger.debug('worker in pool ' + str(len(self._worker_pool)))

        # Call ´_show_data´ when the seach objects ´data_ready´
        # signal is emitted.
        if slot:
            worker.data_ready.connect(slot)
        # Move the search object in it's own thread.
        worker.moveToThread(thread)
        # Stop the thread when the search is finished.
        worker.finished.connect(thread.quit)
        # Call search immediately when the thread starts.
        thread.started.connect(worker.run)
        # Remove references to the worker and it's thread
        # after the thread finished.
        thread.finished.connect(lambda: self._thread_pool.remove(thread))
        thread.finished.connect(lambda: self._worker_pool.remove(worker))
        thread.finished.connect(self._progress.stop)
        thread.finished.connect(self._ui.lbl_prgrss.hide)
        self._logger.debug('start new thread')

        # Ensure api calls are scheduled to one call per second.
        while time() - self._worker_start < 1:
            sleep(0.001)
            app.processEvents()
        # Run
        self._worker_start = time()
        thread.start()
        self._logger.debug('thread started')

    def _rename_file(self, item, new_item):
        """Rename the release directory if it exists and no
           other directory with the same name already exists.
        """

        if not new_item or not item:
            self._logger.debug('skipping: item: %s - new item: %s' %
                (str(item), str(new_item)))
            return

        def isfile_casesensitive(path):
            if not os.path.isfile(path):
                return False
            directory, filename = os.path.split(path)
            return filename in os.listdir(directory)

        def get_data(item, new_item):
            """Get the QListWidgetItem and the release information
               for renaming the release directory.
            """
            data = {}

            filename = unicode(item.text())
            new_filename = "".join(c for c in unicode(new_item.text())
                if c not in r'*?"<>|')
            url = item.url

            self._logger.debug('getting data for: %s' % unicode(item.text()))

            # Append the file extension to the new url if tht file
            # is not a directory.
            if os.path.isfile(url):
                _, ext = os.path.splitext(url)
                new_filename = new_filename + ext

            data['url'] = url
            data['new_url'] = os.path.join(os.path.dirname(url), new_filename)
            data['new_filename'] = new_filename
            data['item'] = item

            self._logger.debug('data: %s' % data)

            return data

        try:
            # Dictionary containing the information to rename the
            # release directory.
            data = get_data(item, new_item)

            if data['url'] == data['new_url']:
                self._logger.warn('skipping: old filename equals new filename')
                return
            if not os.path.exists(data['url']):
                self._logger.warn('file does not exists: %s' % data['url'])
                return
            if isfile_casesensitive(data['new_url']):
                self._logger.warn('file already exists')
                return

            self._logger.debug('rename file from: %s to: %s' %
                (data['url'], data['new_url']))

            # Rename the directory.
            os.rename(data['url'], data['new_url'])
            # Show the new filename in the QListWidgetItem.
            data['item'].setText(data['new_filename'])
            data['item'].url = data['new_url']

        except Exception:
            self._logger.error(traceback.format_exc())

    def _rename(self):
        """Rename files with the new filenames build according to
           the user defined syntax from discogs data. Use the list
           widgets as data source / model to get the pathes for
           the renamed files and the new filenames.
        """

        def get_items(i):
            return self._ui.lst_ld.item(i), self._ui.lst_nw.item(i)

        def update_dir_url(track_item, new_url):
            old_url = os.path.dirname(track_item.url)

            self._logger.debug('updating track url: %s to %s' %
                (old_url, new_url))
            track_item.url = track_item.url.replace(old_url, new_url)

        self._logger.debug('start renaming')

        try:
            indices = range(self._ui.lst_ld.count())
            # Get a list of tuples of all elements of the local file
            # listwidgetitems and the data listwidgetitems.
            items = list(map(get_items, indices))
            # Sort the item list to hold the release item as the last element.
            items = sorted(items, key=lambda x: x[0].type, reverse=True)

            # Rename track files and release directory.
            for item in items:
                self._rename_file(item[0], item[1])

            # Update the directory url of the tracks.
            for track_item in items[:-1]:
                update_dir_url(track_item[0], items[-1][0].url)

        except Exception:
            self._logger.error(traceback.format_exc())

    def _set_tags(self):
        """Set the meta tags in the audio files from the
           discogs data.
        """

        def set_image():
            img_data = None
            with open(os.path.join(path_), 'rb') as f:
                img_data = f.read()

        self._logger.debug('start setting tags')

        for i in range(self._ui.lst_ld.count()):
            try:
                item = self._ui.lst_nw.item(i)
                if not item or getattr(item, 'type') == 'release':
                    continue
                filepath = self._ui.lst_ld.item(i).url
                self._logger.debug('set tags for: ' + item.text())

                data, track = item.data, item.track

                map_empty = ['unknown', 'Unknown', 'UNKNOWN']

                t = self._tagger(filepath)
                t.artist = data.get('artist').lower() or 'unknown'
                t.title = track.get('title').lower() or 'unknown'
                t.album = data.get('title').lower() or 'unknown'
                t.year = data.get('year') if not data.get('year') \
                    in map_empty else None
                t.genre = data.get('genres').lower() or 'unknown'
                try:
                    t.track = int(track.get('index'))
                except:
                    t.track = self._track_index
                t.comments = 'tagged with discopy'
                t.country = data.get('country').lower() or 'unknown'
                t.labels = data.get('label').lower() or 'unknown'
                t.save()
                self._track_index += 1

            except Exception:
                self._logger.error(traceback.format_exc())
                self._track_index = 1
            
        self._logger.debug('finished setting tags')
        self._track_index = 0

    def _get_tags(self):
        """Set the meta tags in the audio files from the
           discogs data.
        """
        self._logger.debug('getting tags')

        for i in range(self._ui.lst_ld.count()):
            try:
                filepath = self._ui.lst_ld.item(i).url
                if os.path.isdir(filepath):
                    continue
                t = self._tagger(filepath)
                if t.album:
                    return unicode(t.album).lower()

            except Exception:
                self._logger.error(traceback.format_exc())
            self._logger.debug('finished getting tags')

    def _set_img_download_path(self, release_id):
        # Get path from the release item in local list.
        path_ = None
        for i in range(self._ui.lst_ld.count()):
            item_ld = self._ui.lst_ld.item(i)
            if getattr(item_ld, 'type') == 'release':
                path_ = item_ld.url
        self._img_download_pathes[release_id] = path_
        self._logger.debug('set image download path for release: %s to: %s'
            % (str(release_id), path_))

    def _get_images(self):
        """Download the release artwork from the discogs api.
        """
        self._logger.debug('get images')

        def move_img(release_id, imagepath, new_filename):
            """Move the image from the temp directory to
               the release directory.
            """
            newdir = self._img_download_pathes.get(release_id) or 'none'
            new_imagepath = os.path.join(newdir, new_filename)
            self._logger.debug('moving image: %s to: %s' %
                (imagepath, new_imagepath))
            # Move the image to the potentially renamed directory.
            try:
                os.rename(imagepath, new_imagepath)
            except Exception:
                self._logger.error('could not move image')

        def get_image_data():
            # Get the image urls via the first item in the
            # result list that contains the image data.
            images = []
            release_id = 0
            for i in range(self._ui.lst_nw.count()):
                item_nw = self._ui.lst_nw.item(i)
                if hasattr(item_nw, 'data'):
                    images = item_nw.data.get('images')
                    release_id = item_nw.data.get('id')
                    break
            self._logger.debug('getting image data for release: %s' %
                (str(release_id),))
            return (release_id, images)

        def download_images(images, release_id):
            """Download all images to the temporary image directory and then
               move them to the renamed release directory.
            """
            self._ui.btn_imgs.setEnabled(False)
            try:
                for i, image in enumerate(images):

                    # URI for the download..
                    uri = image.get('uri')
                    self._logger.debug('download ' + uri)

                    # Get the filename for the temporary storage.
                    temp_img_dir = resource_path(os.path.join(TMP_IMG_DIR,
                        str(release_id)))
                    filename = os.path.basename(uri)
                    download_path = os.path.join(temp_img_dir, filename)
                    # Name fot the new image passed to the image move function.
                    _, ext = os.path.splitext(filename)
                    imagename = 'artwork_' + str(i + 1).zfill(2).lower() + ext

                    # Ensure the temporary download directory exists.
                    if not os.path.isdir(temp_img_dir):
                        os.makedirs(temp_img_dir)

                    # Download the image in a worker thread.
                    self._image_handler.get_file(download_path, uri)
                    move_img(release_id, download_path, imagename)

            except Exception:
                self._logger.error(traceback.format_exc())

        # disable the rename button during image download process.
        # self._ui.btn_rnm.setEnabled(False)

        release_id, img_data = get_image_data()
        self._set_img_download_path(release_id)
        self._run_worker(lambda: self._ui.btn_imgs.setEnabled(True),
            download_images, img_data, release_id)

    def _toggle_search_buttons(self):
        """Toggle the button.
            @param btn: The button to be toggled.
        """
        self._ui.btn_srch.setEnabled(not self._ui.btn_srch.isEnabled())
        self._ui.btn_nxt.setEnabled(not self._ui.btn_nxt.isEnabled())
        self._ui.btn_prv.setEnabled(not self._ui.btn_prv.isEnabled())

    def _set_query(self, qlineedit):
        """Set the search query for discogs api calls. Get the
           query type to be used to determine which api resource
           should be called. Query types are stored in the
           listwidgets itself due to a lack of a model.
        Possible query types:
            url:             search for releases by id.
            release_name:     search for releases by name.
            barcode:         search for release by barcode.
        @param qlineedit: QLineEdit to get the query and query type.
        """
        self._query = unicode(qlineedit.text()).strip()
        self._query_type = qlineedit.query_type
        self._logger.debug('setting query: ' + self._query)
        self._logger.debug('setting query-type: ' + self._query_type)

    def _set_focus(self, qlineedit=None):
        """Visual support for the search query line edits.
        """
        self._ui.lndt_url.setStyleSheet("color: rgb(200, 200, 200);")
        self._ui.lndt_rls.setStyleSheet("color: rgb(200, 200, 200);")
        self._ui.lndt_brcde.setStyleSheet("color: rgb(200, 200, 200);")
        if qlineedit:
            qlineedit.setStyleSheet("color: rgb(0, 0, 0); \
                background: rgb(255,255,255);")

    def _check_network(self):
        """Check if a network connection is available.
        """
        try:
            urllib2.urlopen(CHCK_NTWRK, timeout=1)
            return True

        except urllib2.URLError:
            return False

    def keyPressEvent(self, event):
        key = event.key()
        if key == 81 or key == 87:
            self._save_syntax()
            sys.exit(0)

    def _save_syntax(self):
        self._logger.debug('save_syntax')
        release_syntax = unicode(self._ui.lndt_f_sntx.text())
        track_syntax = unicode(self._ui.lndt_t_sntx.text())
        syntax = {'track_syntax': track_syntax,
            'release_syntax': release_syntax}

        path_ = resource_path(os.path.join(STNGS, SNTX_STNGS))
        with open(path_, 'w') as outfile:
            json.dump(syntax, outfile)

    def _set_syntax(self):
        release_syntax = None
        track_syntax = None

        path_ = resource_path(os.path.join(STNGS, SNTX_STNGS))
        with open(path_) as json_data:
            data = json.load(json_data)
            json_data.close()
            release_syntax = data.get('release_syntax')
            track_syntax = data.get('track_syntax')

        if release_syntax:
            self._ui.lndt_f_sntx.setText(unicode(release_syntax))
        else:
            self._ui.lndt_f_sntx.setText(RLS_SNTX)

        if track_syntax:
            self._ui.lndt_t_sntx.setText(unicode(track_syntax))
        else:
            self._ui.lndt_t_sntx.setText(TRCK_SNTX)

if __name__ == "__main__":
    logpath = os.path.join(expanduser("~"), 'discopy')
    if not os.path.isdir(logpath):
        os.makedirs(logpath)
    log_file = os.path.join(logpath, 'discopy.log')
    logger = logging.getLogger('discopy.main')
    file_log_handler = logging.FileHandler(log_file)
    logger.addHandler(file_log_handler)
    stderr_log_handler = logging.StreamHandler()
    bash_formatter = logging.Formatter(fmt='%(threadName)s | '
                '%(filename)s: %(lineno)d | %(levelname)s: %(message)s')
    stderr_log_handler.setFormatter(bash_formatter)
    logger.addHandler(stderr_log_handler)
    logger.setLevel(logging.DEBUG)
    logger.debug('hello discopy')

    app = QtGui.QApplication(sys.argv)
    iconpath = resource_path(os.path.join(ICN_DIR, 'discopy.ico'))

    start = time()
    splashpath = resource_path(os.path.join(ICN_DIR, SPLSH_SCRN))
    splash = QtGui.QSplashScreen(QtGui.QPixmap(splashpath))
    splash.show()
    while time() - start < 2:
        sleep(0.001)
        app.processEvents()

    win = DiscoPy(Ui_MainWindow(), Client('discopy/0.1', CONSUMER_KEY,
        CONSUMER_SECRET, TOKEN, SECRET), NameBuilder(), TagData, ImageHandler())
    win.setWindowIcon(QtGui.QIcon(iconpath))
    splash.finish(win)

    # import ctypes
    # appid = 'discopy.0.1'
    # ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    win.center()
    win.show()
    sys.exit(app.exec_())
