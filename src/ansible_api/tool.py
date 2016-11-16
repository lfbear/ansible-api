#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import time
import json
import logging
from ansible_api import __version__

__all__ = ['Tool']


class Tool(object):

    LOGGER = None

    @staticmethod
    def init_logger(path):
        log_formatter = "%(asctime)s | %(levelname)s - %(message)s"
        date_formatter = "%Y-%m-%d %H:%M:%S"
        if path:
            logging.basicConfig(filename=path, level=logging.DEBUG,
                                format=log_formatter, datefmt=date_formatter)
        else:
            logging.basicConfig(level=logging.DEBUG,
                                format=log_formatter, datefmt=date_formatter)

        Tool.LOGGER = logging.getLogger('ansible-api_%s' % __version__)
        Tool.LOGGER.setLevel(logging.NOTSET)

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
