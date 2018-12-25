#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible and ansible-runner
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import json
import logging
import os
from . import __version__

__all__ = ['Tool']


class Tool(object):
    LOGGER = None

    @staticmethod
    def init_logger(path):
        log_formatter = "%(asctime)s | %(levelname)s - %(message)s"
        date_formatter = "%Y-%m-%d %H:%M:%S"
        log_formatter = logging.Formatter(fmt=log_formatter, datefmt=date_formatter)
        err_handler = logging.handlers.TimedRotatingFileHandler('/var/log/ansible-api.err', when='midnight')
        err_handler.setFormatter(log_formatter)
        err_handler.setLevel(logging.WARNING)
        if isinstance(path, str) and os.path.exists(os.path.dirname(path)):
            Tool.LOGGER = logging.getLogger('ansible-api.%s' % __version__)
            log_handler = logging.handlers.TimedRotatingFileHandler(path, when='midnight')
            log_handler.setFormatter(log_formatter)
            Tool.LOGGER.addHandler(log_handler)
            Tool.LOGGER.addHandler(err_handler)
            Tool.LOGGER.setLevel(logging.DEBUG)
            Tool.LOGGER.propagate = False  # disable console output
        else:
            logging.basicConfig(level=logging.DEBUG,
                                format=log_formatter, datefmt=date_formatter)
            Tool.LOGGER = logging.getLogger('ansible-api.%s' % __version__)

    @staticmethod
    def getmd5(str):
        import hashlib
        m = hashlib.md5()
        m.update(str.encode('utf-8'))
        return m.hexdigest()

    @staticmethod
    def jsonal(data):
        return json.dumps(data)

    @staticmethod
    def parsejson(string):
        return json.loads(string.decode('utf-8'))
