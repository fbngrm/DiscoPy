# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from start_dialog_ui import StartDialogUi
from rename_dialog_ui import RenameDialogUi


class StartDialog(QtGui.QDialog):
    def __init__(self, settingsHandler, parent=None):
        QtGui.QDialog.__init__(self, parent)
        # Init start dialog
        self.settingsHandler = settingsHandler
        self.ui = StartDialogUi()
        self.ui.setupUi(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Signals
        self.ui.continueButton.clicked.connect(self._close)
        self.show()

    def _close(self):
        settings_data = {'init_dialog': not self.ui.checkBox.isChecked()}
        self.settingsHandler.data = settings_data
        self.close()


class RenameDialog(QtGui.QDialog):
    def __init__(self, settingsHandler, parent=None):
        QtGui.QDialog.__init__(self, parent)
        # Init start dialog
        self.settingsHandler = settingsHandler
        self.ui = RenameDialogUi()
        self.ui.setupUi(self)

    def close_dialog(self):
        settings_data = {'rename_dialog': not self.ui.checkBox.isChecked()}
        self.settingsHandler.data = settings_data
        self.close()
