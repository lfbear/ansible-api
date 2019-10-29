#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible
# Base on ansible-runner and sanic
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

import os
import logging
from . import __version__
from .config import Config

__all__ = ['Tool']


class Tool(object):
    LOGGER = None

    @staticmethod
    def init_logger(path):
        log_format = "%(asctime)s | %(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        log_formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
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
                                format=log_format, datefmt=date_format)
            Tool.LOGGER = logging.getLogger('ansible-api.%s' % __version__)

    @staticmethod
    def encrypt_sign(*args):
        all_str = ''
        for item in args:
            if isinstance(item, str):
                all_str += item
        if Config.get('sign_mode') == 'sha256':
            return Tool.sign_by_sha256(all_str)
        else:  # md5 for default, only for compatibility. Strongly not recommended
            return Tool.sign_by_md5(all_str)

    @staticmethod
    def sign_by_md5(string):
        import hashlib
        m = hashlib.md5()
        m.update(string.encode('utf-8'))
        return m.hexdigest()

    @staticmethod
    def sign_by_sha256(string):
        import hashlib
        m = hashlib.sha256()
        m.update(string.encode('utf-8'))
        return m.hexdigest()
