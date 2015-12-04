# -*- coding: utf-8 -*-
import os
import logging
from logging.handlers import RotatingFileHandler
from constants import HOME, LOG_DIR, LOG_FILE, MAX_LOG_SIZE

def setup_logging():
    logpath = os.path.abspath(os.path.join(HOME, LOG_DIR))
    if not os.path.isdir(logpath):
        os.makedirs(logpath)
    log_file = os.path.join(logpath, LOG_FILE)
    logger = logging.getLogger('discopy.main')
    file_formatter = logging.Formatter(fmt='%(threadName)s | %(filename)s: %(lineno)d | %(levelname)s: %(message)s')
    file_handler = RotatingFileHandler(
        log_file, maxBytes=MAX_LOG_SIZE, backupCount=3, encoding='UTF-8')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    stderr_log_handler = logging.StreamHandler()
    bash_formatter = logging.Formatter(fmt='%(threadName)s | %(filename)s: %(lineno)d | %(levelname)s: %(message)s')
    stderr_log_handler.setFormatter(bash_formatter)
    logger.addHandler(stderr_log_handler)
    logger.setLevel(logging.DEBUG)
    logger.debug('hello discopy')
