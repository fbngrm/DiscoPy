# -*- coding: utf-8 -*-
import logging
from PyQt4 import QtCore


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
        self._logger.debug(
            'thread id of worker: ' +
            str(QtCore.QThread.currentThreadId())
            )
        self.data_ready.emit(data)
        self.finished.emit()
