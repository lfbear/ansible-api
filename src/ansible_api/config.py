#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible
# Base on ansible-runner and sanic
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear, pgder

try:
    import ConfigParser
except ImportError:  # python 3
    import configparser as ConfigParser

__all__ = ['Config']


class Config(object):
    cfg_path = '/etc/ansible/api.cfg'
    host = '127.0.0.1'
    port = 8765
    sign_key = 'YOUR_SIGNATURE_KEY_HERE'
    log_path = '/var/log/ansible-api.log'
    allow_ip = []
    ws_sub = []
    workers = 1  # default is one worker, multi-worker will case BUG of websocket broadcast
    timeout = 3600  # timeout for waiting response

    dir_script = ''
    dir_playbook = ''

    def __init__(self):
        cf = ConfigParser.ConfigParser()
        cf.read(Config.cfg_path)
        try:
            cf.options('default')
        except:
            pass
        else:
            self.host = cf.get('default', 'host') if cf.has_option('default', 'host') else Config.host
            self.port = int(cf.get('default', 'port')) if cf.has_option('default', 'port') else Config.port
            self.sign_key = cf.get('default', 'sign_key') if cf.has_option('default', 'sign_key') else Config.sign_key
            self.log_path = cf.get('default', 'log_path') if cf.has_option('default', 'log_path') else Config.log_path
            self.allow_ip = cf.get('default', 'allow_ip').split() if cf.has_option('default',
                                                                                   'allow_ip') else Config.allow_ip
            self.workers = int(cf.get('default', 'workers')) if cf.has_option('default', 'workers') else Config.workers
            self.ws_sub = cf.get('default', 'ws_sub').split() if cf.has_option('default', 'ws_sub') else Config.ws_sub
            self.timeout = int(cf.get('default', 'timeout')) if cf.has_option('default', 'timeout') else Config.timeout

        try:
            cf.options('directory')
        except:
            pass
        else:
            self.dir_script = cf.get('directory', 'script') if cf.has_option('directory',
                                                                             'script') else Config.dir_script
            self.dir_playbook = cf.get('directory', 'playbook') if cf.has_option('directory',
                                                                                 'playbook') else Config.dir_playbook

    @staticmethod
    def get(attr):
        cfg = Config()
        return getattr(cfg, attr, '')
