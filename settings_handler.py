#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import json
import sys
from shutil import copy
from constants import HOME, STNGS_DIR, STNGS_FILE

if os.name == 'posix':
    LOG_DIR = '.discopy'
else:
    LOG_DIR = 'discopy'


def resource_path(relative):
    return os.path.join(getattr(
        sys, '_MEIPASS', os.path.abspath(".")), relative)


class SettingsHandler(object):

    def __init__(self):
        self._data = None
        self.path = os.path.abspath(
            os.path.join(HOME, LOG_DIR, STNGS_DIR, STNGS_FILE))

    def setup(self):
        # Ensure the settings directory exists in users home dir.
        settings_dir = os.path.abspath(os.path.join(HOME, LOG_DIR, STNGS_DIR))
        if not os.path.isdir(settings_dir):
            os.makedirs(settings_dir)

        # Copy the settings file to home dir of the user.
        settings_file = os.path.join(settings_dir, STNGS_FILE)
        if not os.path.isfile(settings_file):
            settings_src = resource_path(os.path.join(STNGS_DIR, STNGS_FILE))
            try:
                copy(settings_src, settings_file)
            except Exception:
                pass

    @property
    def data(self):
        try:
            if not self._data:
                with open(self.path) as json_data:
                    self._data = json.load(json_data)
                    json_data.close()
            return self._data
        except Exception:
            return {}

    @data.setter
    def data(self, data):
        try:
            dump_data = self.data
            for key, value in data.items():
                dump_data[key] = value
            with open(self.path, 'w') as json_data:
                json.dump(dump_data, json_data)
                json_data.close()
                self._data = dump_data
        except Exception:
            pass
