# -*- coding: utf-8 -*-
import os
from os.path import expanduser


CHCK_NTWRK = 'http://www.google.com'
PRGRSS_ICN = 'progress.gif'
ICN_DIR = 'icons'
SPLSH_SCRN = 'discopy_800px.png'
THMB_DIR = 'thumbs'
TMP_IMG_DIR = 'images'
RLS_SNTX = "artist - release [labels year]"
TRCK_SNTX = "index track"
MAX_LOG_SIZE = 100000
STNGS_DIR = 'settings'
STNGS_FILE = 'settings.json'
HOME = expanduser("~")
LOG_FILE = 'discopy.log'

if os.name == 'posix':
    LOG_DIR = '.discopy'
else:
    LOG_DIR = 'discopy'
