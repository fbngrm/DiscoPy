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

import os
import json
import sys
from shutil import copy
from constants import HOME, STNGS_DIR, STNGS_FILE

if os.name == 'posix':
    LOG_DIR = '.discopy'
else:
    LOG_DIR = 'discopy'

STNGS_PATH = os.path.abspath(
    os.path.join(HOME, LOG_DIR, STNGS_DIR, STNGS_FILE))


def resource_path(relative):
    return os.path.join(getattr(
        sys, '_MEIPASS', os.path.abspath(".")), relative)


class SettingsHandler(object):

    def __init__(self):
        self._data = None

        if os.path.isfile(STNGS_PATH):
            self.path = STNGS_PATH
        else:
            self.path = resource_path(
                os.path.join(LOG_DIR, STNGS_DIR, STNGS_FILE))

    def setup(self):
        # Ensure the settings directory exists.
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
