#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import yaml
import time

from jinja2 import Environment, meta
from tornado.web import RequestHandler, HTTPError, asynchronous
import tornado.gen
from concurrent import futures
from ansible_api.tool import Tool
from ansible_api.config import Config
from ansible_api.api import Api


__all__ = [
    'Main',
    'FileList',
    'FileReadWrite',
    'FileExist',
    'ParseVarsFromFile',
    'Command',
    'Playbook',
]

executor = futures.ThreadPoolExecutor(Config.Get('thread_pool_size'))


class Controller(RequestHandler):

    def __init__(self, application, request, **kwargs):
        super(Controller, self).__init__(application, request, **kwargs)
        if len(Config.Get('allow_ip')) and self.request.remote_ip not in Config.Get('allow_ip'):
            raise HTTPError(403, 'Your ip(%s) is forbidden' %
                            self.request.remote_ip)


class Main(Controller):

    def get(self):
        self.write(Tool.jsonal(
            {'message': "Hello, I am Ansible Api", 'rc': Tool.ERRCODE_NONE}))


class AsyncTest(Controller):

    @tornado.gen.coroutine
    def get(self):
        msg = yield executor.submit(self.test, 10)
        self.write(Tool.jsonal(
            {'message': msg, 'rc': Tool.ERRCODE_NONE}))
        self.finish()

    def test(self, s):
        time.sleep(s)
        return 'i have slept 10 s'


class Command(Controller):

    def get(self):
        self.write(Tool.jsonal(
            {'error': "Forbidden in get method", 'rc': Tool.ERRCODE_SYS}))

    @tornado.gen.coroutine
    def post(self):
        data = Tool.parsejson(self.request.body)
        badcmd = ['reboot', 'su', 'sudo', 'dd',
                  'mkfs', 'shutdown', 'half', 'top']
        name = data['n']
        module = data['m']
        arg = data['a']
        target = data['t']
        sign = data['s']
        sudo = True if data['r'] else False
        forks = data.get('c', 50)
        cmdinfo = arg.split(' ', 1)
        Tool.reporting('run: {0}, {1}, {2}, {3}, {4}, {5}'.format(
            name, target, module, arg, sudo, forks))
        hotkey = name + module + target + Config.Get('sign_key')
        check_str = Tool.getmd5(hotkey)
        if sign != check_str:
            self.write(Tool.jsonal(
                {'error': "Sign is error", 'rc': Tool.ERRCODE_BIZ}))
        else:
            if module in ('shell', 'command') and cmdinfo[0] in badcmd:
                self.write(Tool.jsonal(
                    {'error': "This is danger shell: " + cmdinfo[0], 'rc': Tool.ERRCODE_BIZ}))
            else:
                try:
                    response = yield executor.submit(Api.runCmd, name=name, target=target, module=module, arg=arg, sudo=sudo, forks=forks)
                except BaseException as e:
                    Tool.reporting(
                        "A {0} error occurs: {1}".format(type(e), e.message))
                    self.write(Tool.jsonal(
                        {'error': e.message, 'rc': Tool.ERRCODE_BIZ}))
                else:
                    self.write(response)


class Playbook(Controller):

    @tornado.gen.coroutine
    def post(self):
        data = Tool.parsejson(self.request.body)
        hosts = data['h']
        sign = data['s']
        yml_file = data['f']
        forks = data.get('c', 50)
        if not hosts or not yml_file or not sign:
            self.write(Tool.jsonal(
                {'error': "Lack of necessary parameters", 'rc': Tool.ERRCODE_SYS}))
        else:
            hotkey = hosts + yml_file + Config.Get('sign_key')
            check_str = Tool.getmd5(hotkey)
            if sign != check_str:
                self.write(Tool.jsonal(
                    {'error': "Sign is error", 'rc': Tool.ERRCODE_BIZ}))
            else:
                myvars = {'hosts': hosts}
                # injection vars in playbook (rule: vars start with "v_" in
                # post data)
                for(k, v) in data.items():
                    if k[0:2] == "v_":
                        myvars[k[2:]] = v
                yml_file = Config.Get('dir_playbook') + yml_file
                if os.path.isfile(yml_file):
                    Tool.reporting("playbook: {0}, host: {1}, forks: {2}".format(
                        yml_file, hosts, forks))
                    try:
                        response = yield executor.submit(Api.runPlaybook, yml_file=yml_file, myvars=myvars, forks=forks)
                    except BaseException as e:
                        Tool.reporting(
                            "A {0} error occurs: {1}".format(type(e), e.message))
                        self.write(Tool.jsonal(
                            {'error': e.message, 'rc': Tool.ERRCODE_BIZ}))
                    else:
                        self.write(response)

                else:
                    self.write(Tool.jsonal(
                        {'error': "yml file(" + yml_file + ") is not existed", 'rc': Tool.ERRCODE_SYS}))


class FileList(Controller):

    def get(self):
        path = self.get_argument('type', 'script')
        sign = self.get_argument('sign', '')
        allows = ['script', 'playbook', 'authkeys']
        if path in allows:
            hotkey = path + Config.Get('sign_key')
            check_str = Tool.getmd5(hotkey)
            if sign != check_str:
                self.write(Tool.jsonal(
                    {'error': "Sign is error", 'rc': Tool.ERRCODE_BIZ}))
            else:
                path_var = Config.Get('dir_' + path)
                if os.path.exists(path_var):
                    Tool.reporting("read file list: " + path_var)
                    dirs = os.listdir(path_var)
                    self.write({'list': dirs})
                else:
                    self.write(Tool.jsonal(
                        {'error': "Path is not existed", 'rc': Tool.ERRCODE_SYS}))
        else:
            self.write(Tool.jsonal(
                {'error': "Wrong type in argument", 'rc': Tool.ERRCODE_SYS}))


class FileReadWrite(Controller):

    def get(self):
        path = self.get_argument('type', 'script')
        file_name = self.get_argument('name')
        sign = self.get_argument('sign', '')
        allows = ['script', 'playbook', 'authkeys']
        if path in allows:
            hotkey = path + file_name + Config.Get('sign_key')
            check_str = Tool.getmd5(hotkey)
            if sign != check_str:
                self.write(Tool.jsonal(
                    {'error': "Sign is error", 'rc': Tool.ERRCODE_BIZ}))
            else:
                file_path = Config.Get('dir_' + path) + file_name
                if os.path.isfile(file_path):
                    file_object = open(file_path)
                    try:
                        Tool.reporting("read from file: " + file_path)
                        contents = file_object.read()
                        self.write(Tool.jsonal({'content': contents}))
                    finally:
                        file_object.close()
                else:
                    self.write(Tool.jsonal(
                        {'error': "No such file in script path", 'rc': Tool.ERRCODE_BIZ}))
        else:
            self.write(Tool.jsonal(
                {'error': "Wrong type in argument", 'rc': Tool.ERRCODE_SYS}))

    def post(self):
        data = Tool.parsejson(self.request.body)
        path = data['p']
        filename = data['f']
        content = data['c']
        sign = data['s']
        if not filename or not content or not sign or path \
                not in ['script', 'playbook', 'authkeys']:
            self.write(Tool.jsonal(
                {'error': "Lack of necessary parameters", 'rc': Tool.ERRCODE_SYS}))
        hotkey = path + filename + Config.Get('sign_key')
        check_str = Tool.getmd5(hotkey)
        if sign != check_str:
            self.write(Tool.jsonal(
                {'error': "Sign is error", 'rc': Tool.ERRCODE_BIZ}))
        else:
            file_path = Config.Get('dir_' + path) + filename
            if path == 'authkeys':  # allow mkdir in this mode
                dir_name = os.path.dirname(file_path)
                os.path.isdir(dir_name) == False and os.mkdir(dir_name)
            file_object = open(file_path, 'w')
            file_object.write(content)
            file_object.close()
            Tool.reporting("write to file: " + file_path)
            self.write(Tool.jsonal({'ret': True}))


class FileExist(Controller):

    def get(self):
        path = self.get_argument('type', 'script')
        file_name = self.get_argument('name')
        sign = self.get_argument('sign', '')
        allows = ['script', 'playbook']
        if path in allows:
            hotkey = path + file_name + Config.Get('sign_key')
            check_str = Tool.getmd5(hotkey)
            if sign != check_str:
                self.write(Tool.jsonal(
                    {'error': "Sign is error", 'rc': Tool.ERRCODE_BIZ}))
            else:
                file_path = Config.Get('dir_' + path) + file_name
                Tool.reporting("file exist? " + file_path)
                if os.path.isfile(file_path):
                    self.write(Tool.jsonal({'ret': True}))
                else:
                    self.write(Tool.jsonal({'ret': False}))
        else:
            self.write(Tool.jsonal(
                {'error': "Wrong type in argument", 'rc': Tool.ERRCODE_SYS}))


class ParseVarsFromFile(Controller):

    def get(self):
        file_name = self.get_argument('name')
        sign = self.get_argument('sign', '')
        hotkey = file_name + Config.Get('sign_key')
        check_str = Tool.getmd5(hotkey)
        if sign != check_str:
            self.write(Tool.jsonal(
                {'error': "Sign is error", 'rc': Tool.ERRCODE_BIZ}))
        else:
            file_path = Config.Get('dir_playbook') + file_name
            if os.path.isfile(file_path):
                file_object = open(file_path)
                env = Environment()
                try:
                    Tool.reporting("parse from file: " + file_path)
                    contents = file_object.read()
                    ignore_vars = []
                    yamlstream = yaml.load(contents)
                    for yamlitem in yamlstream:
                        if isinstance(yamlitem, dict) and yamlitem.get('vars_files', []) and len(yamlitem['vars_files']) > 0:
                            for vf in yamlitem['vars_files']:
                                tmp_file = Config.Get('dir_playbook') + vf
                                if os.path.isfile(tmp_file):
                                    tmp_vars = yaml.load(file(tmp_file))
                                    if isinstance(tmp_vars, dict):
                                        ignore_vars += tmp_vars.keys()
                    if len(ignore_vars) > 0:
                        Tool.reporting("skip vars: " + ",".join(ignore_vars))
                    ast = env.parse(contents)
                    var = list(meta.find_undeclared_variables(ast))
                    var = list(set(var).difference(set(ignore_vars)))
                    self.write({'vars': var})
                finally:
                    file_object.close()
            else:
                self.write(Tool.jsonal(
                    {'error': "No such file in script path", 'rc': Tool.ERRCODE_SYS}))
