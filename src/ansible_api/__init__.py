#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear
# Version: 0.1.1 at 2016.8.17

from __future__ import (print_function)

import os
import json
import time
import ConfigParser
import tornado.web
from jinja2 import Environment, meta
import api4ansible2


class Tool(object):
    LOG_REPORT_HANDERL = None

    @staticmethod
    def getmd5(str):
        import hashlib
        m = hashlib.md5()
        m.update(str)
        return m.hexdigest()

    @staticmethod
    def reporting(str):
        report = time.strftime('%Y-%m-%d %H:%M:%S',
                               time.gmtime()) + ' | ' + str
        if Tool.LOG_REPORT_HANDERL:
            Tool.LOG_REPORT_HANDERL.write(report + "\n")
            Tool.LOG_REPORT_HANDERL.flush()
        else:
            print(report)


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


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.write("Hello, I am Ansible Api")


class FileListHandler(tornado.web.RequestHandler):

    def get(self):
        path = self.get_argument('type', 'script')
        sign = self.get_argument('sign', '')
        allows = ['script', 'playbook', 'authkeys']
        if path in allows:
            hotkey = path + Config.Get('sign_key')
            check_str = Tool.getmd5(hotkey)
            if sign != check_str:
                self.write("Sign is error")
            else:
                path_var = Config.Get('dir_' + path)
                if os.path.exists(path_var):
                    Tool.reporting("read file list: " + path_var)
                    dirs = os.listdir(path_var)
                    self.write({'list': dirs})
                else:
                    self.write('Path is not existed')
        else:
            self.write('Wrong type in argument')


class FileRWHandler(tornado.web.RequestHandler):

    def get(self):
        path = self.get_argument('type', 'script')
        file_name = self.get_argument('name')
        sign = self.get_argument('sign', '')
        allows = ['script', 'playbook', 'authkeys']
        if path in allows:
            hotkey = path + file_name + Config.Get('sign_key')
            check_str = Tool.getmd5(hotkey)
            if sign != check_str:
                self.write("Sign is error")
            else:
                file_path = Config.Get('dir_' + path) + file_name
                if os.path.isfile(file_path):
                    file_object = open(file_path)
                    try:
                        Tool.reporting("read from file: " + file_path)
                        contents = file_object.read()
                        self.write({'content': contents})
                    finally:
                        file_object.close()
                else:
                    self.write('No such file in script path')
        else:
            self.write('Wrong type in argument')

    def post(self):
        data = json.loads(self.request.body)
        path = data['p']
        filename = data['f']
        content = data['c']
        sign = data['s']
        if not filename or not content or not sign or path \
                not in ['script', 'playbook', 'authkeys']:
            self.write('Lack of necessary parameters')
        hotkey = path + filename + Config.Get('sign_key')
        check_str = Tool.getmd5(hotkey)
        if sign != check_str:
            self.write("Sign is error")
        else:
            file_path = Config.Get('dir_' + path) + filename
            if path == 'authkeys':  # allow mkdir in this mode
                dir_name = os.path.dirname(file_path)
                os.path.isdir(dir_name) == False and os.mkdir(dir_name)
            file_object = open(file_path, 'w')
            file_object.write(content)
            file_object.close()
            Tool.reporting("write to file: " + file_path)
            self.write({'ret': True})


class FileExistHandler(tornado.web.RequestHandler):

    def get(self):
        path = self.get_argument('type', 'script')
        file_name = self.get_argument('name')
        sign = self.get_argument('sign', '')
        allows = ['script', 'playbook']
        if path in allows:
            hotkey = path + file_name + Config.Get('sign_key')
            check_str = Tool.getmd5(hotkey)
            if sign != check_str:
                self.write("Sign is error")
            else:
                file_path = Config.Get('dir_' + path) + file_name
                Tool.reporting("file exist? " + file_path)
                if os.path.isfile(file_path):
                    self.write({'ret': True})
                else:
                    self.write({'ret': False})
        else:
            self.write('Wrong type in argument')


class ParseVarsFromFile(tornado.web.RequestHandler):

    def get(self):
        file_name = self.get_argument('name')
        sign = self.get_argument('sign', '')
        hotkey = file_name + Config.Get('sign_key')
        check_str = Tool.getmd5(hotkey)
        if sign != check_str:
            self.write("Sign is error")
        else:
            file_path = Config.Get('dir_playbook') + file_name
            if os.path.isfile(file_path):
                file_object = open(file_path)
                env = Environment()
                try:
                    Tool.reporting("parse from file: " + file_path)
                    contents = file_object.read()
                    ast = env.parse(contents)
                    var = list(meta.find_undeclared_variables(ast))
                    self.write({'vars': var})
                finally:
                    file_object.close()
            else:
                self.write('No such file in script path')


class CommandHandler(tornado.web.RequestHandler):

    def get(self):
        self.write("Forbidden in get method")

    def post(self):
        data = json.loads(self.request.body)
        badcmd = ['reboot', 'su', 'sudo', 'dd',
                  'mkfs', 'shutdown', 'half', 'top']
        module = data['m']
        arg = data['a']
        target = data['t']
        sign = data['s']
        sudo = True if data['r'] else False
        forks = data.get('c', 50)
        cmdinfo = arg.split(' ', 1)
        Tool.reporting('run: {0}, {1}, {2}, {3}, {4}'.format(
            target, module, arg, sudo, forks))
        hotkey = module + target + Config.Get('sign_key')
        check_str = Tool.getmd5(hotkey)
        if sign != check_str:
            self.write("Sign is error")
        else:
            if cmdinfo[0] in badcmd:
                self.write("This is danger shell(" + cmdinfo[0] + ")")
            else:
                try:
                    aa2 = api4ansible2.Api()
                    response = aa2.runCmd(target, module, arg, sudo, forks)
                except BaseException, e:
                    Tool.reporting(
                        "A {0} error occurs: {1}".format(type(e), e.message))
                    self.write({'error': e.message})
                else:
                    self.write(response)


class PlaybookHandler(tornado.web.RequestHandler):

    def post(self):
        data = json.loads(self.request.body)
        hosts = data['h']
        sign = data['s']
        yml_file = data['f']
        forks = data.get('c', 50)
        if not hosts or not yml_file or not sign:
            self.write("Lack of necessary parameters")
            return False
        hotkey = hosts + yml_file + Config.Get('sign_key')
        check_str = Tool.getmd5(hotkey)
        if sign != check_str:
            self.write("Sign is error")
            return False

        myvars = {'hosts': hosts}
        # injection vars in playbook (rule: vars start with "v_" in post data)
        for(k, v) in data.items():
            if k[0:2] == "v_":
                myvars[k[2:]] = v

        yml_file = Config.Get('dir_playbook') + yml_file
        if os.path.isfile(yml_file):
            Tool.reporting("playbook: {0}, host: {1}, forks: {2}".format(
                yml_file, hosts, forks))
            try:
                aa2 = api4ansible2.Api()
                response = aa2.runPlaybook(yml_file, myvars, forks)
            except BaseException, e:
                Tool.reporting(
                    "A {0} error occurs: {1}".format(type(e), e.message))
                self.write({'error': e.message})
            else:
                self.write(response)

        else:
            self.write("yml file(" + yml_file + ") is not existed")
