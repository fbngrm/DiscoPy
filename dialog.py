# -*- coding: utf-8 -*-

"""
Copyright 2015 Fabian Grimme

This file is part of DiscoPy.

DiscoPy is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
DiscoPy is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with D
"""

import os
import chardet
from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8

    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)

except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

SPPRTD = ['.mp3', '.aac', '.alac',
    '.ogg', '.asf', '.mpc',
    '.aiff', '.opus', '.mp4',
    '.wav', '.flac', '.aif',
    '.mid', '.m4a', '.ape'
        ]
ITM_TPS = {
    "release": "record_30px.png",
    "track": "track_30px.png"
}


class ClickableLabel(QtGui.QLabel):

    def __init(self, parent):
        QtGui.QLabel.__init__(self, parent)

    def mouseReleaseEvent(self, event):
        self.emit(QtCore.SIGNAL('clicked'))


class DNDListWidget(QtGui.QListWidget):

    drop_finished = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(DNDListWidget, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setIconSize(QtCore.QSize(100, 100))
        self._drop_data = []
        self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.connect(self, QtCore.SIGNAL('dropped'), self._data_dropped)
        self.connect(self, QtCore.SIGNAL('delete'), self._remove_item)
        self.setFrameShadow(QtGui.QFrame.Plain)
        self.setFrameShape(QtGui.QFrame.NoFrame)
        self.setFrameStyle(0)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.acceptProposedAction()
        else:
            super(DNDListWidget, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        super(DNDListWidget, self).dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            links = []
            for url in event.mimeData().urls():
                path = unicode(url.toLocalFile())
                if not os.path.isdir(path):
                    continue
                else:
                    self.clear()
                    files = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
                    for file_ in files:
                        name, ext = os.path.splitext(file_)
                        if ext not in SPPRTD:
                            continue
                        links.append(file_)
                    links.append(path)
                    break
            self.emit(QtCore.SIGNAL("dropped"), links)
            event.acceptProposedAction()
        else:
            super(DNDListWidget, self).dropEvent(event)

    def clear(self):
        for i in range(self.count(), 0, -1):
            self.takeItem(i - 1)

    def _data_dropped(self, data):
        if len(data):
            release_data = None
            track_data = []
            for file_ in data:
                name, ext = os.path.splitext(file_)
                if ext in SPPRTD:
                    track_data.append(file_)
                else:
                    release_data = file_

            # Drop tracks first.
            for track in track_data:
                self.data_dropped(os.path.basename(track), "track", url=track)
            # Order in ascending alphbetical order.
            self.sortItems(QtCore.Qt.AscendingOrder)

            # Drop the release to be the first widget.
            self.data_dropped(os.path.basename(data[-1]), "release", url=release_data)

            # Color the list widget background alternatingly.
            self.color_items()
            self.drop_finished.emit()

    def data_dropped(self, data, type_, editable=False, meta=None, url=None):
        # Get the icon for the listwidgetitem.
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'icons', ITM_TPS[type_]))
        icon = QtGui.QIcon(icon_path)

        # Create a listwidgetitem.
        item = QtGui.QListWidgetItem(icon, data, parent=None, type=0)
        item.setSizeHint(QtCore.QSize(0, 35))
        item.url = url
        item.type = type_
        if editable:
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.insertItem(0, item)

        # due to the lack of model we have to store meta information for id tagging in the items.
        if type_ == "release" and meta:
            item.data = meta['release']
        elif meta:
            item.data = meta['release']
            item.track = meta['track']

    def color_items(self):
        for i in range(self.count(), 0, -1):
            i = i - 1
            if i % 2 != 0:
                self.item(i).setBackgroundColor(QtGui.QColor(220, 220, 220))
                self.item(i).setTextColor(QtGui.QColor(50, 50, 50))
            else:
                self.item(i).setBackgroundColor(QtGui.QColor(245, 245, 245))
                self.item(i).setTextColor(QtGui.QColor(50, 50, 50))

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Backspace or key == QtCore.Qt.Key_Delete:
            self.emit(QtCore.SIGNAL("delete"))

    def _remove_item(self):
        self.takeItem(self.currentRow())


class LineEdit(QtGui.QLineEdit):
    text_modified = QtCore.pyqtSignal(str, str)
    query = QtCore.pyqtSignal(QtGui.QLineEdit)
    focus = QtCore.pyqtSignal(QtGui.QLineEdit)

    def __init__(self, contents='', parent=None):
        super(LineEdit, self).__init__(contents, parent)
        self.editingFinished.connect(self._editing_finished)
        self.textChanged.connect(self._text_changed)
        self._before = contents
        self.setFrame(False)
        self.setMinimumSize(QtCore.QSize(0, 30))

    def _text_changed(self, text):
        if not self.hasFocus():
            self._before = text

    def _editing_finished(self):
        before, after = self._before, self.text()
        if before != after:
            self._before = after
            self.text_modified.emit(before, after)
            if self.query:
                self.query.emit(self)

    def valueChanged(self, text):
        if QtGui.QApplication.clipboard().text() == text:
            self.pasteEvent(text)

    def focusInEvent(self, event):
        self.focus.emit(self)
        super(LineEdit, self).focusInEvent(event)


class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1206, 814)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout_2 = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))

        self.btn_hlp = QtGui.QPushButton(self.centralwidget)
        self.btn_hlp.setMinimumSize(QtCore.QSize(0, 0))
        self.btn_hlp.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btn_hlp.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.btn_hlp.setObjectName(_fromUtf8("btn_hlp"))
        self.horizontalLayout.addWidget(self.btn_hlp)

        spacerItem = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)

        self.lbl_prgrss = QtGui.QLabel(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_prgrss.sizePolicy().hasHeightForWidth())
        self.lbl_prgrss.setSizePolicy(sizePolicy)
        self.lbl_prgrss.setMinimumSize(QtCore.QSize(150, 0))
        self.lbl_prgrss.setText(_fromUtf8(""))
        self.lbl_prgrss.setObjectName(_fromUtf8("lbl_prgrss"))
        self.horizontalLayout.addWidget(self.lbl_prgrss)

        spacerItem1 = QtGui.QSpacerItem(25, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)

        self.btn_srch = QtGui.QPushButton(self.centralwidget)
        self.btn_srch.setMinimumSize(QtCore.QSize(0, 0))
        self.btn_srch.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btn_srch.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.btn_srch.setObjectName(_fromUtf8("btn_srch"))
        self.horizontalLayout.addWidget(self.btn_srch)

        self.btn_prv = QtGui.QPushButton(self.centralwidget)
        self.btn_prv.setEnabled(True)
        self.btn_prv.setObjectName(_fromUtf8("btn_prv"))
        self.horizontalLayout.addWidget(self.btn_prv)

        self.btn_nxt = QtGui.QPushButton(self.centralwidget)
        self.btn_nxt.setEnabled(True)
        self.btn_nxt.setCheckable(False)
        self.btn_nxt.setObjectName(_fromUtf8("btn_nxt"))

        self.horizontalLayout.addWidget(self.btn_nxt)
        spacerItem2 = QtGui.QSpacerItem(25, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)

        self.btn_imgs = QtGui.QPushButton(self.centralwidget)
        self.btn_imgs.setEnabled(True)
        self.btn_imgs.setObjectName(_fromUtf8("btn_imgs"))
        self.horizontalLayout.addWidget(self.btn_imgs)

        self.btn_tgs = QtGui.QPushButton(self.centralwidget)
        self.btn_tgs.setEnabled(True)
        self.btn_tgs.setObjectName(_fromUtf8("btn_tgs"))
        self.horizontalLayout.addWidget(self.btn_tgs)

        self.btn_rnm = QtGui.QPushButton(self.centralwidget)
        self.btn_rnm.setEnabled(True)
        self.btn_rnm.setMinimumSize(QtCore.QSize(0, 0))
        self.btn_rnm.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btn_rnm.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.btn_rnm.setObjectName(_fromUtf8("btn_rnm"))
        self.horizontalLayout.addWidget(self.btn_rnm)

        self.gridLayout_2.addLayout(self.horizontalLayout, 4, 1, 1, 1)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))

        spacerItem3 = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem3, 1, 5, 1, 1)

        self.label_4 = QtGui.QLabel(self.centralwidget)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout.addWidget(self.label_4, 2, 3, 1, 1)

        self.lbl_gnr = QtGui.QLabel(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_gnr.sizePolicy().hasHeightForWidth())
        self.lbl_gnr.setSizePolicy(sizePolicy)
        self.lbl_gnr.setMinimumSize(QtCore.QSize(290, 0))
        self.lbl_gnr.setMaximumSize(QtCore.QSize(290, 16777215))
        self.lbl_gnr.setText(_fromUtf8(""))
        self.lbl_gnr.setObjectName(_fromUtf8("lbl_gnr"))
        self.gridLayout.addWidget(self.lbl_gnr, 4, 4, 1, 1)

        self.lbl_lbl = QtGui.QLabel(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_lbl.sizePolicy().hasHeightForWidth())
        self.lbl_lbl.setSizePolicy(sizePolicy)
        self.lbl_lbl.setMinimumSize(QtCore.QSize(290, 0))
        self.lbl_lbl.setMaximumSize(QtCore.QSize(290, 16777215))
        self.lbl_lbl.setText(_fromUtf8(""))
        self.lbl_lbl.setObjectName(_fromUtf8("lbl_lbl"))
        self.gridLayout.addWidget(self.lbl_lbl, 3, 4, 1, 1)

        self.lndt_url = LineEdit(parent=self.centralwidget)
        self.lndt_url.setAutoFillBackground(True)
        self.lndt_url.setObjectName(_fromUtf8("lndt_url"))
        self.gridLayout.addWidget(self.lndt_url, 1, 0, 1, 2)
        spacerItem4 = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem4, 1, 7, 1, 1)

        self.lbl_cvr = ClickableLabel(self.centralwidget)
        self.lbl_cvr.setMinimumSize(QtCore.QSize(150, 150))
        self.lbl_cvr.setMaximumSize(QtCore.QSize(150, 150))
        self.lbl_cvr.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.lbl_cvr.setFrameShape(QtGui.QFrame.NoFrame)
        self.lbl_cvr.setText(_fromUtf8(""))
        self.lbl_cvr.setObjectName(_fromUtf8("lbl_cvr"))
        self.gridLayout.addWidget(self.lbl_cvr, 1, 6, 5, 1)

        self.lbl_url = QtGui.QLabel(self.centralwidget)
        self.lbl_url.setObjectName(_fromUtf8("lbl_url"))
        self.gridLayout.addWidget(self.lbl_url, 0, 0, 1, 2)

        self.lndt_f_sntx = LineEdit(parent=self.centralwidget)
        self.lndt_f_sntx.setAutoFillBackground(True)
        self.lndt_f_sntx.setObjectName(_fromUtf8("lndt_f_sntx"))
        self.gridLayout.addWidget(self.lndt_f_sntx, 5, 0, 1, 1)
        self.lbl_f_sntx = QtGui.QLabel(self.centralwidget)
        self.lbl_f_sntx.setObjectName(_fromUtf8("lbl_f_sntx"))
        self.gridLayout.addWidget(self.lbl_f_sntx, 4, 0, 1, 1)

        self.lndt_t_sntx = LineEdit(parent=self.centralwidget)
        self.lndt_t_sntx.setAutoFillBackground(True)
        self.lndt_t_sntx.setObjectName(_fromUtf8("lndt_t_sntx"))
        self.gridLayout.addWidget(self.lndt_t_sntx, 5, 1, 1, 1)
        self.lbl_t_sntx = QtGui.QLabel(self.centralwidget)
        self.lbl_t_sntx.setObjectName(_fromUtf8("lbl_t_sntx"))
        self.gridLayout.addWidget(self.lbl_t_sntx, 4, 1, 1, 1)

        self.lndt_brcde = LineEdit(parent=self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lndt_brcde.sizePolicy().hasHeightForWidth())
        self.lndt_brcde.setSizePolicy(sizePolicy)
        self.lndt_brcde.setAutoFillBackground(True)
        self.lndt_brcde.setObjectName(_fromUtf8("lndt_brcde"))
        self.gridLayout.addWidget(self.lndt_brcde, 3, 1, 1, 1)

        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 2, 1, 1, 1)

        self.lndt_rls = LineEdit(parent=self.centralwidget)
        self.lndt_rls.setAutoFillBackground(True)
        self.lndt_rls.setObjectName(_fromUtf8("lndt_rls"))
        self.gridLayout.addWidget(self.lndt_rls, 3, 0, 1, 1)

        self.label_5 = QtGui.QLabel(self.centralwidget)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 3, 3, 1, 1)

        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)

        self.label_3 = QtGui.QLabel(self.centralwidget)
        self.label_3.setMinimumSize(QtCore.QSize(50, 0))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 1, 3, 1, 1)

        self.label_7 = QtGui.QLabel(self.centralwidget)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.gridLayout.addWidget(self.label_7, 5, 3, 1, 1)

        self.lbl_rls = QtGui.QLabel(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_rls.sizePolicy().hasHeightForWidth())
        self.lbl_rls.setSizePolicy(sizePolicy)
        self.lbl_rls.setMinimumSize(QtCore.QSize(290, 0))
        self.lbl_rls.setMaximumSize(QtCore.QSize(290, 16777215))
        self.lbl_rls.setText(_fromUtf8(""))
        self.lbl_rls.setObjectName(_fromUtf8("lbl_rls"))
        self.gridLayout.addWidget(self.lbl_rls, 2, 4, 1, 1)

        self.lbl_yr = QtGui.QLabel(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_yr.sizePolicy().hasHeightForWidth())
        self.lbl_yr.setSizePolicy(sizePolicy)
        self.lbl_yr.setMinimumSize(QtCore.QSize(290, 0))
        self.lbl_yr.setMaximumSize(QtCore.QSize(290, 16777215))
        self.lbl_yr.setText(_fromUtf8(""))
        self.lbl_yr.setObjectName(_fromUtf8("lbl_yr"))
        self.gridLayout.addWidget(self.lbl_yr, 5, 4, 1, 1)
        self.lbl_artst = QtGui.QLabel(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_artst.sizePolicy().hasHeightForWidth())

        self.lbl_artst.setSizePolicy(sizePolicy)
        self.lbl_artst.setMinimumSize(QtCore.QSize(290, 0))
        self.lbl_artst.setMaximumSize(QtCore.QSize(290, 16777215))
        self.lbl_artst.setStyleSheet(_fromUtf8(""))
        self.lbl_artst.setText(_fromUtf8(""))
        self.lbl_artst.setObjectName(_fromUtf8("lbl_artst"))
        self.gridLayout.addWidget(self.lbl_artst, 1, 4, 1, 1)
        self.label_6 = QtGui.QLabel(self.centralwidget)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout.addWidget(self.label_6, 4, 3, 1, 1)

        spacerItem5 = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem5, 3, 2, 1, 1)

        self.gridLayout_2.addLayout(self.gridLayout, 0, 1, 1, 1)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.gridLayout_2.addLayout(self.horizontalLayout_3, 2, 1, 1, 1)
        self.gridLayout_3 = QtGui.QGridLayout()
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))

        self.lst_ld = DNDListWidget(self.centralwidget)
        self.lst_ld.setObjectName(_fromUtf8("lst_ld"))
        self.gridLayout_3.addWidget(self.lst_ld, 1, 0, 1, 1)

        spacerItem6 = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.gridLayout_3.addItem(spacerItem6, 0, 0, 1, 1)

        self.lst_nw = DNDListWidget(self.centralwidget)
        self.lst_nw.setMinimumSize(QtCore.QSize(0, 0))
        self.lst_nw.setObjectName(_fromUtf8("lst_nw"))
        self.gridLayout_3.addWidget(self.lst_nw, 1, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout_3, 1, 1, 1, 1)

        spacerItem7 = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.gridLayout_2.addItem(spacerItem7, 3, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1206, 28))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.lndt_brcde.query_type = 'barcode'
        self.lndt_rls.query_type = 'release'
        self.lndt_url.query_type = 'url'

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "DiscoPy", None))
        self.btn_hlp.setText(_translate("MainWindow", "Help", None))
        self.btn_srch.setText(_translate("MainWindow", "Search", None))
        self.btn_prv.setText(_translate("MainWindow", "Previous", None))
        self.btn_nxt.setText(_translate("MainWindow", "Next", None))
        self.btn_imgs.setText(_translate("MainWindow", "Get Artwork", None))
        self.btn_tgs.setText(_translate("MainWindow", "Set Tags", None))
        self.btn_rnm.setText(_translate("MainWindow", "Rename", None))
        self.label_4.setText(_translate("MainWindow", "Release:", None))
        self.lbl_url.setText(_translate("MainWindow", "Discogs URL", None))
        self.lbl_f_sntx.setText(_translate("MainWindow", "Release Syntax", None))
        self.lbl_t_sntx.setText(_translate("MainWindow", "Track Syntax", None))
        self.label.setText(_translate("MainWindow", "Barcode", None))
        self.label_5.setText(_translate("MainWindow", "Labels:", None))
        self.label_2.setText(_translate("MainWindow", "Release Name", None))
        self.label_3.setText(_translate("MainWindow", "Artists:", None))
        self.label_7.setText(_translate("MainWindow", "Year:", None))
        self.label_6.setText(_translate("MainWindow", "Genres:", None))
