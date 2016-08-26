#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ConfigParser

__all__ = ['Config']


class Config(object):
    host = '127.0.0.1'
    port = 8765
    sign_key = 'YOUR_SIGNATURE_KEY_HERE'
    log_path = '/var/log/ansible-api.log'

    dir_script = ''
    dir_playbook = ''
    dir_authkeys = ''

    def __init__(self):
        cf = ConfigParser.ConfigParser()

        cf.read('/etc/ansible/api.cfg')
        try:
            cf.options('default')
        except:
            pass
        else:
            if (cf.get('default', 'host')):
                self.host = cf.get('default', 'host')
            if (cf.get('default', 'port')):
                self.port = cf.get('default', 'port')
            if (cf.get('default', 'sign_key')):
                self.sign_key = cf.get('default', 'sign_key')
            if (cf.get('default', 'log_path')):
                self.log_path = cf.get('default', 'log_path')

        try:
            cf.options('directory')
        except:
            pass
        else:
            if (cf.get('directory', 'script')):
                self.dir_script = cf.get('directory', 'script')
            if (cf.get('directory', 'playbook')):
                self.dir_playbook = cf.get('directory', 'playbook')
            if (cf.get('directory', 'authkeys')):
                self.dir_authkeys = cf.get('directory', 'authkeys')

    @staticmethod
    def Get(attr):
        cfg = Config()
        return getattr(cfg, attr, '')
