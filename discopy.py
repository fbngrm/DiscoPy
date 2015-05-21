#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright 2015 Fabian Grimme

This file is part of DiscoPy.

DiscoPy is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
DiscoPy is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with DiscoPy. If not, see <http://www.gnu.org/licenses/>.
"""

import re
import os
import sys
import json
from time import time, sleep
import traceback
from PyQt4 import QtGui, QtCore
from dialog import Ui_MainWindow
from namebuilder import NameBuilder
from tagdata import TagData
from imageloader import ImageHandler
from discogs_client import Client
import urllib2

sys.setdefaultencoding('utf-8')

CONSUMER_KEY = u'YCHnZAvCExYsNdToncxg'
CONSUMER_SECRET = u'GjutzgPzBwTPkSOUmVEAHsQnfZKWKmhZ'
TOKEN = u'AyEcThzRVKwWlKtkgYWObTDbxcpfqiQoVYpKpOuL'
SECRET = u'zNMTqemlkZfPwpMsIpkVciVqBpOpFaNPlLzADVnu'
CHCK_NTWRK = 'http://74.125.228.100'
PRGRSS_ICN = 'progress.gif'
ICN_DIR = 'icons'
SPLSH_SCRN = 'discopy_800px.png'
THMB_DIR = 'thumbs'
STNGS = 'settings'
SNTX_STNGS = 'syntax.json'
RLS_SNTX = "artist - release [labels year]"
TRCK_SNTX = "index track"


def resource_path(relative):
    return os.path.join(getattr(sys, '_MEIPASS', os.path.abspath(".")), relative)
cert_path = resource_path('cacert.pem')

# Set `REQUESTS_CA_BUNDLE` path for `requests` module pem file if not in development mode.
if os.path.exists(cert_path):
    os.environ['REQUESTS_CA_BUNDLE'] = cert_path


class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    data_ready = QtCore.pyqtSignal(object)

    def __init__(self, function, *args, **kwargs):
        super(Worker, self).__init__()
        logging.debug('create worker')
        self._function = function
        self._args = args
        self._kwargs = kwargs

    @QtCore.pyqtSlot()
    def run(self):
        logging.debug('call ' + self._function.__name__)
        data = self._function(*self._args, **self._kwargs)
        logging.debug('finished ' + self._function.__name__)
        logging.debug('thread id of worker: ' + str(QtCore.QThread.currentThreadId()))
        self.data_ready.emit(data)
        self.finished.emit()


class DiscoPy(QtGui.QMainWindow):

    def __init__(self, ui, client, name_builder, tagdata, image_handler, parent=None):
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
        # Index for the thumb preview of artwork images.
        self._thumb_index = 0
        # Animation to show download progress
        self._progress = None
        # Keep references to worker threads while threads are running
        self._thread_pool = []
        # Refereances to worker objects
        self._worker_pool = []
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
        self.connect(self._ui.lbl_cvr, QtCore.SIGNAL('clicked'), self._get_thumb)
        # Init
        self._set_focus()
        # Initialize the progress animation
        imagepath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'icons', PRGRSS_ICN))
        self._progress = QtGui.QMovie(imagepath, QtCore.QByteArray(), self)
        self._progress.setCacheMode(QtGui.QMovie.CacheAll)
        self._progress.setSpeed(100)
        self._ui.lbl_prgrss.setMovie(self._progress)
        # Initialize the syntax line edits.
        self._set_syntax()

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
            self._discogs_data_index = (self._discogs_data_index + step) % (len(self._discogs_data))
            logging.debug('skip results - step: %d - index: %d' % (step, self._discogs_data_index))
            # Disable the search buttons during search process.
            self._toggle_search_buttons()
            # Skip and parse the search results in a worker thread. Show data when the ´data_ready´ signal is emitted.
            self._run_worker(self._show_data, self._parse_data)

    def _search(self):
        """Move the search to a worker thread. Show data in the list widget when the request returns.
        """
        if not self._query:
            return
        logging.debug('search for: ' + self._query)
        # Disable the search buttons during search process.
        self._toggle_search_buttons()
        # Run the search in a worker thread. Show search results when the ´data_ready´ signal is emitted.
        self._run_worker(self._show_data, self._get_data)

    def _get_data(self):
        """Send a discogs api request according to the request type. The request type is defined by the search query provided by the user input.
        """
        logging.debug('get data')
        self._discogs_data, self._discogs_data_index = [], 0
        try:
            if self._query_type == 'url':
                type_, id_ = self._parse_url(self._query)
                # Search for a master release by id.
                if type_ == 'master':
                    logging.debug('get master by id: ' + self._query)
                    self._discogs_data.append(self._client.master(int(id_)))
                # Search for a release by id.
                elif type_ == 'release':
                    logging.debug('get release by id: ' + self._query)
                    self._discogs_data.append(self._client.release(int(id_)))
            # Search for a release by name.
            elif self._query_type == 'release':
                logging.debug('search release by name: ' + self._query)
                self._discogs_data = self._client.search(self._query, type='release')
            # Search for a release by barcode.
            elif self._query_type == 'barcode':
                logging.debug('get release by barcode: ' + self._query)
                self._discogs_data = self._client.search(barcode=self._query)

            # Parse the data returned by discogs api.
            if len(self._discogs_data):
                self._parse_data()

        except Exception:
            logging.error(traceback.format_exc())

    def _parse_data(self):
        """Parse the discogs response to a simple data object. Since the discgos client uses lazy instatiation this is needed to move all api requests to one worker thread.
        """
        # Get data from the discogs seach results for the current page specified by ´self._discogs_data_index´.
        discogs_data = self._discogs_data[self._discogs_data_index]

        # Set id of the currently displayed release.
        self._parsed_data_id = discogs_data.id

        logging.debug('parse data for release id: %s' % (str(self._parsed_data_id)))

        # Reset the thumb index for artwork preview.
        self._thumb_index = 0

        # Check if the release is has already been parsed.
        if self._parsed_data_id in self._parsed_data.keys():
            return
        else:
            self._parsed_data[self._parsed_data_id] = {'tracks': {}, 'release': {}}

        # Get the syntax to build the release and track names.
        t_syntax = unicode(self._ui.lndt_t_sntx.text())
        d_syntax = unicode(self._ui.lndt_f_sntx.text())

        # Parse discogs_data.
        release_data = {}
        release_data['title'] = getattr(discogs_data, 'title') or 'Unknown' if hasattr(discogs_data, 'title') else 'Unknown'
        release_data['year'] = str(getattr(discogs_data, 'year') or 'Unknown') if hasattr(discogs_data, 'year') else 'Unknown'
        release_data['country'] = getattr(discogs_data, 'country') or 'Unknown' if hasattr(discogs_data, 'country') else 'Unknown'

        release_data['genres'] = ' ,'.join(genre for genre in getattr(discogs_data, 'genres') or ['Unknown']) if hasattr(discogs_data, 'genres') else 'Unknown'

        #release_data['artist'] = getattr(discogs_data.artists[0], 'name') or 'Unknown' if hasattr(discogs_data, 'artists') else 'Unknown'

        release_data['artist'] = ' ,'.join(getattr(artist, 'name') for artist in getattr(discogs_data, 'artists') or ['Unknown']) if hasattr(discogs_data, 'artists') else 'Unknown'

        #release_data['label'] = getattr(discogs_data.labels[0], 'name') if hasattr(discogs_data, 'labels') else 'Unknown'

        release_data['label'] = ' ,'.join(getattr(label, 'name') for label in getattr(discogs_data, 'labels') or ['Unknown']) if hasattr(discogs_data, 'labels') else 'Unknown'

        release_data['images'] = getattr(discogs_data, 'images') or [] if hasattr(discogs_data, 'images') else []

        release_data['id'] = getattr(discogs_data, 'id') if hasattr(discogs_data, 'id') else 'Unknown ID'

        # Build release name.
        release_name = self._name_builder.build_name(d_syntax, release_data, None)
        release_data['name'] = release_name

        # Store the parsed release data for the current search.
        self._parsed_data[discogs_data.id]['release'] = release_data

        # Parse tracklist data
        if hasattr(discogs_data, 'tracklist'):
            for track in discogs_data.tracklist:
                track_data = {}
                track_data['title'] = track.title if hasattr(track, 'title') else 'Unknown Title'
                track_data['index'] = str(track.position) if hasattr(track, 'position') else ''
                # Build track name.
                track_name = self._name_builder.build_name(t_syntax, release_data, track_data)
                track_data['name'] = track_name
                # Store the track data.
                self._parsed_data[self._parsed_data_id]['tracks'][track_name] = track_data
        logging.debug('parsing finished')

    def _show_data(self):
        """initialize the search list widget with the parsed data from the discogs search results.
        """
        logging.debug('show data fior release id: %s' % (str(self._parsed_data_id)))

        # Get data for the current release.
        release_data = self._parsed_data[self._parsed_data_id]

        # Clear list first.
        self._ui.lst_nw.clear()

        # Set list widgets for all tracks in the parsed data.
        for track in release_data['tracks'].values():
            release_data['track'] = track
            self._ui.lst_nw.data_dropped(track['name'], "track", meta=release_data, editable=True)

        self._ui.lst_nw.sortItems(QtCore.Qt.AscendingOrder)

        # Set list widget for the release.
        self._ui.lst_nw.data_dropped(release_data['release']['name'], "release", meta=release_data, editable=True)

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

        logging.debug('finished showing data')

    def _parse_url(self, url):
        """Parse the discogs url to determine the release type and extract the release id.
        """
        logging.debug('parse url: ' + unicode(url))
        search = re.search('(master|release){1}/{1}(\d*)', url, re.UNICODE)
        if search:
            logging.debug('type: %s - id: %s' % (search.group(1), str(search.group(2))))
            return (search.group(1), search.group(2))
        else:
            logging.debug('type: None, id: None')
            return (None, None)

    def _get_thumb(self):
        """Get a thumbnail preview of the artwork.
        """

        try:
            # Get data for the current release.
            release_data = self._parsed_data[self._parsed_data_id]['release']

            logging.debug('get thumb for release id: ' + str(release_data['id']))
            label = self._ui.lbl_cvr
            uri150 = release_data['images'][self._thumb_index]['uri150']
            imagename = uri150.split('/')[-1]
            imagedir = resource_path(THMB_DIR)
            if not os.path.exists(imagedir):
                os.makedirs(imagedir)
            imagepath = os.path.join(imagedir, imagename)
            # Download preview image in a worker thread if it does not exist.
            if not os.path.isfile(imagepath):
                self._run_worker(lambda: self._show_thumb(label, imagepath), self._image_handler.get_file, imagepath, uri150)
            else:
                self._show_thumb(label, imagepath)

        except Exception:
            logging.error(traceback.format_exc())
        logging.debug('finished getting thumbs')

    def _show_thumb(self, label, imagepath):
        """Show the artwork preview in the preview label.
        """
        logging.debug('show thumb')

        images = self._parsed_data[self._parsed_data_id]['release'].get('images') or []

        if not os.path.isfile(imagepath):
            return
        if len(images):
            label.setPixmap(QtGui.QPixmap(imagepath))
            self._thumb_index = (self._thumb_index + 1) % len(images)

    def _update_list(self):
        """Update the list widget when syntax changes are made in the syntax line edit fields.
        """

        logging.debug('update list')

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
                item.setText(new_txt)

            if not hasattr(item, 'track'):
                continue
            # Update the track widgets.
            if item.type == "track":
                syntax = unicode(self._ui.lndt_t_sntx.text())
                new_txt = self._name_builder.build_name(syntax, item.data, item.track)
                item.setText(new_txt)
        logging.debug('finished updating list')

    def _run_worker(self, slot, function, *args, **kwargs):
        """Provides a g.eneric worker thread.
        @param slot: callback function to be called when the function is finished.
        @param function: callable that should be called from within the worker thread.
        @param args: argument list passed to ´function´.
        @param kwargs: argument dictionary passed to ´function´.
        """

        logging.debug('thread id: ' + str(QtCore.QThread.currentThreadId()))
        self._ui.lbl_prgrss.show()
        self._progress.start()
        # No parent!
        thread = QtCore.QThread()
        # Need to keep a reference to the thread while it is running.
        self._thread_pool.append(thread)
        logging.debug('threads in pool ' + str(len(self._thread_pool)))
        # No parent!
        worker = Worker(function, *args, **kwargs)
        # Need to keep a reference to the worker while it is living inside the worker thread.
        self._worker_pool.append(worker)
        logging.debug('worker in pool ' + str(len(self._worker_pool)))

        # Call ´_show_data´ when the seach objects ´data_ready´ signal is emitted.
        if slot:
            worker.data_ready.connect(slot)
        # Move the search object in it's own thread.
        worker.moveToThread(thread)
        # Stop the thread when the search is finished.
        worker.finished.connect(thread.quit)
        # Call search immediately when the thread starts.
        thread.started.connect(worker.run)
        # Remove references to the worker and it's thread after the thread finished.
        thread.finished.connect(lambda: self._thread_pool.remove(thread))
        thread.finished.connect(lambda: self._worker_pool.remove(worker))
        thread.finished.connect(self._progress.stop)
        thread.finished.connect(self._ui.lbl_prgrss.hide)
        logging.debug('start new thread')
        # Run
        thread.start()
        logging.debug('thread started')

    def _rename_file(self, item, new_item):
        """Rename the release directory if it exists and no other directory with the same name already exists.
        """

        def get_data(item, new_item):
            """Get the QListWidgetItem and the release information for renaming the release directory.
            """
            data = {}

            filename = unicode(item.text())
            new_filename = unicode(new_item.text())
            url = item.url

            # Append the file extension to the new url if tht file is not a directory.
            if os.path.isfile(url):
                _, ext = os.path.splitext(url)
                new_filename = new_filename + ext
            
            new_url = url.replace(filename, new_filename)

            data['url'] = url
            data['new_url'] = new_url
            data['new_filename'] = new_filename
            data['item'] = item

            return data

        try:
            # Dictionary containing the information to rename the release directory.
            data = get_data(item, new_item)

            rename = True

            if data['url'] == data['new_url']:
                rename = False
            if not os.path.exists(data['url']):
                rename = False
            if os.path.exists(data['new_url']):
                rename = False

            if rename:
                logging.debug('rename file from: %s to: %s' % (data['url'], data['new_url']))

                # Rename the directory.
                os.rename(data['url'], data['new_url'])
                # Show the new filename in the QListWidgetItem.
                data['item'].setText(data['new_filename'])
                # Updtae the uri of the QListWidgetItem.
                data['item'].url = data['new_url']

        except Exception:
            logging.error(traceback.format_exc())

    def _rename(self):
        """Rename files with the new filenames build according to the user defined syntax from discogs data. Use the list widgets as data source / model to get the pathes for the renamed files and the new filenames.
        """
        logging.debug('start renaming')

        old_dir_url, new_dir_url = '', ''
        track_items = []

        for i in range(self._ui.lst_ld.count()):

            try:
                item = self._ui.lst_ld.item(i)
                new_item = self._ui.lst_nw.item(i)

                # Rename directory first.
                if getattr(item, 'type') == 'release':
                    logging.debug('rename directory')
                    old_dir_url = item.url
                    self._rename_file(item, new_item)
                    new_dir_url = item.url
                else:
                    track_items.append((item, new_item))

            except Exception:
                logging.error(traceback.format_exc())

        for track_item in track_items:
            # Update the url of the track/file with the new directory name of the release directory.
            track_item[0].url = track_item[0].url.replace(old_dir_url, new_dir_url)
            logging.debug('rename track')
            self._rename_file(track_item[0], track_item[1])


    def _set_tags(self):
        """Set the meta tags in the audio files from the discogs data.
        """
        logging.debug('start setting tags')

        for i in range(self._ui.lst_ld.count()):
            try:
                item = self._ui.lst_nw.item(i)
                if getattr(item, 'type') == 'release':
                    continue
                filepath = self._ui.lst_ld.item(i).url
                logging.debug('set tags for: ' + item.text())

                data, track = item.data, item.track

                t = self._tagger(filepath)
                t.artist = data.get('artist').lower() or 'unknown'
                t.title = track.get('title').lower() or 'unknown'
                t.album = data.get('title').lower() or 'unknown'
                t.year = data.get('year') or None
                t.genre = data.get('genres').lower() or 'unknown'
                t.track = track.get('position') or None
                t.comment = 'tagged with discopy'
                t.country = data.get('country').lower() or 'unknown'
                t.labels = data.get('label').lower() or 'unknown'
                t.save()

            except Exception:
                logging.error(traceback.format_exc())
            logging.debug('finished setting tags')

    def _get_images(self):
        """Download the release artwork from the discogs api.
        """
        logging.debug('get images')

        def get_files(images):
            self._ui.btn_imgs.setEnabled(False)
            try:
                for i, image in enumerate(images):
                    uri = image.get('uri')
                    logging.debug('download ' + uri)
                    filename = 'artwork_' + str(i + 1).zfill(2).lower()
                    _, ext = os.path.splitext(uri)
                    download_path = os.path.join(filepath, filename + str(ext))
                    if not os.path.isdir(filepath):
                        os.makedirs(filepath)
                    self._image_handler.get_file(download_path, uri)
            except Exception:
                logging.error(traceback.format_exc())
            self._ui.btn_imgs.setEnabled(True)

        filepath, item = '', None

        # Get path from the release item in local list.
        for i in range(self._ui.lst_ld.count()):
            item_ld = self._ui.lst_ld.item(i)
            if getattr(item_ld, 'type') == 'release':
                filepath = item_ld.url

        if not filepath:
            return

        # Get the image urls via the first item in the result list that contains the image data.
        for i in range(self._ui.lst_nw.count()):
            item_nw = self._ui.lst_nw.item(i)
            if hasattr(item_nw, 'data'):
                item = item_nw
                break

        if not item:
            return

        # disable the rename button during image download process.
        self._ui.btn_rnm.setEnabled(False)

        images = item.data.get('images') or []
        self._run_worker(lambda: self._ui.btn_rnm.setEnabled(True), get_files, images)

    def _toggle_search_buttons(self):
        """Toggle the button.
            @param btn: The button to be toggled.
        """
        self._ui.btn_srch.setEnabled(not self._ui.btn_srch.isEnabled())
        self._ui.btn_nxt.setEnabled(not self._ui.btn_nxt.isEnabled())
        self._ui.btn_prv.setEnabled(not self._ui.btn_prv.isEnabled())

    def _set_query(self, qlineedit):
        """Set the search query for discogs api calls. Get the query type to be used to determine which api resource should be called. Query types are stored in the listwidgets itself due to a lack of a model.
        Possible query types:
            url:             search for releases by id.
            release_name:     search for releases by name.
            barcode:         search for release by barcode.
        @param qlineedit: QLineEdit to get the query and query type.
        """
        self._query = unicode(qlineedit.text()).strip()
        self._query_type = qlineedit.query_type
        logging.debug('setting query: ' + self._query)
        logging.debug('setting query-type: ' + self._query_type)

    def _set_focus(self, qlineedit=None):
        """Visual support for the search query line edits.
        """
        self._ui.lndt_url.setStyleSheet("color: rgb(200, 200, 200);")
        self._ui.lndt_rls.setStyleSheet("color: rgb(200, 200, 200);")
        self._ui.lndt_brcde.setStyleSheet("color: rgb(200, 200, 200);")
        if qlineedit:
            qlineedit.setStyleSheet("color: rgb(0, 0, 0); background: rgb(255,255,255);")

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
        logging.debug('save_syntax')
        release_syntax = unicode(self._ui.lndt_f_sntx.text())
        track_syntax = unicode(self._ui.lndt_t_sntx.text())
        syntax = {'track_syntax': track_syntax, 'release_syntax': release_syntax}

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
    import logging

    log_file = os.path.abspath(os.path.join(resource_path('..'), 'discopy.log'))
    logging.basicConfig(filename=log_file, level=logging.DEBUG)

    app = QtGui.QApplication(sys.argv)
    start = time()
    iconpath = resource_path(os.path.join(ICN_DIR, SPLSH_SCRN))
    splash = QtGui.QSplashScreen(QtGui.QPixmap(iconpath))
    splash.show()
    while time() - start < 1:
        sleep(0.001)
        app.processEvents()
    win = DiscoPy(Ui_MainWindow(), Client('discopy/0.1', CONSUMER_KEY, CONSUMER_SECRET, TOKEN, SECRET), NameBuilder(), TagData, ImageHandler())
    win.setWindowIcon(QtGui.QIcon(os.path.join(iconpath, 'discopy_30px.png')))
    splash.finish(win)
    win.center()
    win.show()
    logging.info('Run')
    sys.exit(app.exec_())
