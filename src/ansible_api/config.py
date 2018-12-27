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
from tornado.process import cpu_count

__all__ = ['Config']


class Config(object):
    cfg_path = '/etc/ansible/api.cfg'
    host = '127.0.0.1'
    port = 8765
    sign_key = 'YOUR_SIGNATURE_KEY_HERE'
    log_path = '/var/log/ansible-api.log'
    allow_ip = []
    thread_pool_size = cpu_count() // 2     # adapt the number of thread pool size to the number of cpu cores

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
            if cf.has_option('default', 'host'):
                self.host = cf.get('default', 'host')
            if cf.has_option('default', 'port'):
                self.port = cf.get('default', 'port')
            if cf.has_option('default', 'sign_key'):
                self.sign_key = cf.get('default', 'sign_key')
            if cf.has_option('default', 'log_path'):
                self.log_path = cf.get('default', 'log_path')
            if cf.has_option('default', 'allow_ip'):
                self.allow_ip = cf.get('default', 'allow_ip').split()
            if cf.has_option('default', 'thread_pool_size'):
                self.thread_pool_size = cf.get('default', 'thread_pool_size')

        try:
            cf.options('directory')
        except:
            pass
        else:
            if cf.has_option('directory', 'script'):
                self.dir_script = cf.get('directory', 'script')
            if cf.has_option('directory', 'playbook'):
                self.dir_playbook = cf.get('directory', 'playbook')

    @staticmethod
    def get(attr):
        cfg = Config()
        return getattr(cfg, attr, '')
