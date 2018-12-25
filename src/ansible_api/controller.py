#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible and ansible-runner
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear, pgder

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import os
import sys
import time
import yaml
import ansible_runner

from jinja2 import Environment, meta
from tornado.web import RequestHandler, HTTPError

from .tool import Tool
from .config import Config
from .callback import CallBack

__all__ = [
    'Main',
    'FileList',
    'FileReadWrite',
    'FileExist',
    'ParseVarsFromFile',
    'Command',
    'Playbook',
    'AsyncTest',
]


class ErrorCode(object):
    ERRCODE_NONE = 0
    ERRCODE_SYS = 1
    ERRCODE_BIZ = 2


class Controller(RequestHandler):

    def data_received(self, chunk):
        pass

    def __init__(self, application, request, **kwargs):
        Tool.LOGGER.debug("MORE DETAIL: request %s" % request)
        super(Controller, self).__init__(application, request, **kwargs)
        if len(Config.get('allow_ip')) and self.request.remote_ip not in Config.get('allow_ip'):
            raise HTTPError(403, 'Your ip(%s) is forbidden' % self.request.remote_ip)


class Main(Controller):

    def get(self):
        self.finish(Tool.jsonal(
            {'message': "Hello, I am Ansible Api", 'rc': ErrorCode.ERRCODE_NONE}))


class AsyncTest(Controller):

    def get(self):
        self.finish(Tool.jsonal(
            {'message': 'hi test', 'rc': ErrorCode.ERRCODE_NONE}))

    async def test(self):
        time.sleep(10)
        return 'i have slept 10 s'


class Command(Controller):

    def get(self):
        self.finish(Tool.jsonal(
            {'error': "Forbidden in get method", 'rc': ErrorCode.ERRCODE_SYS}))

    async def post(self):  # Change the async method to python3 async, this performance better than gen.coroutine
        data = Tool.parsejson(self.request.body)
        bad_cmd = ['reboot', 'su', 'sudo', 'dd',
                   'mkfs', 'shutdown', 'half', 'top']
        name = data.get('n').encode('utf-8').decode()
        module = data.get('m')
        arg = data.get('a').encode('utf-8').decode()
        target = data.get('t')
        sign = data.get('s')
        sudo = True if data.get('r') else False
        forks = data.get('c', 50)
        cmd_info = arg.split(' ', 1)
        Tool.LOGGER.info('run: {0}, {1}, {2}, {3}, {4}, {5}'.format(
            name, target, module, arg, sudo, forks))
        hot_key = name + module + target + Config.get('sign_key')
        check_str = Tool.getmd5(hot_key)
        if sign != check_str:
            self.finish(Tool.jsonal(
                {'error': "Sign is error", 'rc': ErrorCode.ERRCODE_BIZ}))
        else:
            if module in ('shell', 'command') and cmd_info[0] in bad_cmd:
                self.finish(Tool.jsonal(
                    {'error': "This is danger shell: " + cmd_info[0], 'rc': ErrorCode.ERRCODE_BIZ}))
            else:
                try:
                    cb = CallBack()
                    cb.status_drawer(dict(status='starting', raw=lambda: dict(
                        task_name=module, event='playbook_on_play_start', runner_ident=name,
                        event_data=dict(pattern=target, name=module)),
                        after=lambda: dict(task_list=[module])))
                    response = ansible_runner.interface.run(
                        host_pattern=target, inventory='/etc/ansible/hosts',
                        envvars=dict(PATH=sys.path[0]),
                        ident=name, module=module, module_args=arg,
                        event_handler=cb.event_handler, status_handler=cb.status_handler
                    )
                    # pp = pprint.PrettyPrinter(indent=4)
                    # print('*' * 20)
                    # pp.pprint(cb.get_summary())
                    # print('+' * 20)
                    self.finish(Tool.jsonal(dict(rc=response.rc, detail=cb.get_summary())))
                except Exception as e:
                    Tool.LOGGER.exception(e)
                    self.finish(Tool.jsonal(
                        {'error': str(e), 'rc': ErrorCode.ERRCODE_BIZ}))


class Playbook(Controller):

    async def post(self):
        data = Tool.parsejson(self.request.body)
        Tool.LOGGER.debug("MORE DETAIL: data %s" % data)
        name = data['n'].encode('utf-8').decode()
        hosts = data['h']
        sign = data['s']
        yml_file = data['f'].encode('utf-8').decode()
        forks = data.get('c', 50)
        if not hosts or not yml_file or not sign:
            self.finish(Tool.jsonal(
                {'error': "Lack of necessary parameters", 'rc': ErrorCode.ERRCODE_SYS}))
        else:
            hot_key = name + hosts + yml_file + Config.get('sign_key')
            Tool.LOGGER.debug("MORE DETAIL: hot key %s" % hot_key)
            check_str = Tool.getmd5(hot_key)
            if sign != check_str:
                self.finish(Tool.jsonal(
                    {'error': "Sign is error", 'rc': ErrorCode.ERRCODE_BIZ}))
            else:
                my_vars = {'hosts': hosts}
                # injection vars in playbook (rule: vars start with "v_" in
                # post data)
                for (k, v) in data.items():
                    if k[0:2] == "v_":
                        my_vars[k[2:]] = v
                yml_file = Config.get('dir_playbook') + yml_file

                Tool.LOGGER.debug("MORE DETAIL: yml file %s" % yml_file)
                if os.path.isfile(yml_file):
                    task_list = []
                    with open(yml_file, 'r') as contents:
                        yaml_cnt = yaml.load(contents)
                        if len(yaml_cnt) > 0 and len(yaml_cnt[0].get('tasks', [])) > 0:
                            task_list = [x.get('name', 'unnamed') for x in yaml_cnt[0]['tasks']]
                    Tool.LOGGER.info("playbook: {0}, host: {1}, forks: {2}".format(
                        yml_file, hosts, forks))
                    try:
                        cb = CallBack()
                        cb.event_pepper('playbook_on_play_start', dict(task_list=task_list))
                        response = ansible_runner.interface.run(
                            host_pattern=hosts, inventory='/etc/ansible/hosts',
                            envvars=dict(PATH=sys.path[0]),
                            playbook=yml_file, ident=name, extravars=my_vars,
                            event_handler=cb.event_handler, status_handler=cb.status_handler
                        )
                        # pp = pprint.PrettyPrinter(indent=4)
                        # print('*' * 20)
                        # pp.pprint(cb.get_summary())
                        # print('+' * 20)
                        self.finish(Tool.jsonal(dict(rc=response.rc, detail=cb.get_summary())))
                    except BaseException as e:
                        Tool.LOGGER.exception(e)
                        self.finish(Tool.jsonal(
                            {'error': str(e), 'rc': ErrorCode.ERRCODE_BIZ}))

                else:
                    self.finish(Tool.jsonal(
                        {'error': "yml file(" + yml_file + ") is not existed", 'rc': ErrorCode.ERRCODE_SYS}))


class FileList(Controller):

    async def get(self):
        path = self.get_argument('type', 'script')
        sign = self.get_argument('sign', '')
        allows = ['script', 'playbook']
        if path in allows:
            hot_key = path + Config.get('sign_key')
            check_str = Tool.getmd5(hot_key)
            if sign != check_str:
                self.finish(Tool.jsonal(
                    {'error': "Sign is error", 'rc': ErrorCode.ERRCODE_BIZ}))
            else:
                path_var = Config.get('dir_' + path)
                if os.path.exists(path_var):
                    Tool.LOGGER.info("read file list: " + path_var)
                    dirs = os.listdir(path_var)
                    self.finish({'list': dirs})
                else:
                    self.finish(Tool.jsonal(
                        {'error': "Path is not existed", 'rc': ErrorCode.ERRCODE_SYS}))
        else:
            self.finish(Tool.jsonal(
                {'error': "Wrong type in argument", 'rc': ErrorCode.ERRCODE_SYS}))


class FileReadWrite(Controller):

    async def get(self):
        path = self.get_argument('type', 'script')
        file_name = self.get_argument('name')
        sign = self.get_argument('sign', '')
        allows = ['script', 'playbook']
        if path in allows:
            hot_key = path + file_name + Config.get('sign_key')
            check_str = Tool.getmd5(hot_key)
            if sign != check_str:
                self.finish(Tool.jsonal(
                    {'error': "Sign is error", 'rc': ErrorCode.ERRCODE_BIZ}))
            else:
                file_path = Config.get('dir_' + path) + file_name
                if os.path.isfile(file_path):
                    contents = self.read_file(file_path)
                    self.finish(Tool.jsonal({'content': contents}))
                else:
                    self.finish(Tool.jsonal(
                        {'error': "No such file in script path", 'rc': ErrorCode.ERRCODE_BIZ}))
        else:
            self.finish(Tool.jsonal(
                {'error': "Wrong type in argument", 'rc': ErrorCode.ERRCODE_SYS}))

    @classmethod
    def read_file(cls, file_path):
        file_object = open(file_path)
        try:
            Tool.LOGGER.info("read from file: " + file_path)
            contents = file_object.read()
        except BaseException:
            Tool.LOGGER.error("failed in reading from file: " + file_path)
            contents = ''
        finally:
            file_object.close()
        return contents

    async def post(self):
        data = Tool.parsejson(self.request.body)
        path = data['p']
        filename = data['f']
        content = data['c'].encode('utf-8').decode()
        sign = data['s']
        if not filename or not content or not sign or path \
                not in ['script', 'playbook']:
            self.finish(Tool.jsonal(
                {'error': "Lack of necessary parameters", 'rc': ErrorCode.ERRCODE_SYS}))
        hot_key = path + filename + Config.get('sign_key')
        check_str = Tool.getmd5(hot_key)
        if sign != check_str:
            self.finish(Tool.jsonal(
                {'error': "Sign is error", 'rc': ErrorCode.ERRCODE_BIZ}))
        else:
            file_path = Config.get('dir_' + path) + filename
            result = self.write_file(file_path, content)
            self.finish(Tool.jsonal({'ret': result}))

    def write_file(self, file_path, content):
        result = True
        try:
            file_object = open(file_path, 'w')
            file_object.write(content)
        except BaseException as err:
            result = False
            Tool.LOGGER.error("failed in writing to file: " + file_path)
        else:
            Tool.LOGGER.info("write to file: " + file_path)
            file_object.close()
        return result


class FileExist(Controller):

    def get(self):
        path = self.get_argument('type', 'script')
        file_name = self.get_argument('name')
        sign = self.get_argument('sign', '')
        allows = ['script', 'playbook']
        if path in allows:
            hot_key = path + file_name + Config.get('sign_key')
            check_str = Tool.getmd5(hot_key)
            if sign != check_str:
                self.finish(Tool.jsonal(
                    {'error': "Sign is error", 'rc': ErrorCode.ERRCODE_BIZ}))
            else:
                file_path = Config.get('dir_' + path) + file_name
                Tool.LOGGER.info("file exist? " + file_path)
                if os.path.isfile(file_path):
                    self.finish(Tool.jsonal({'ret': True}))
                else:
                    self.finish(Tool.jsonal({'ret': False}))
        else:
            self.finish(Tool.jsonal(
                {'error': "Wrong type in argument", 'rc': ErrorCode.ERRCODE_SYS}))


class ParseVarsFromFile(Controller):

    async def get(self):
        file_name = self.get_argument('name')
        sign = self.get_argument('sign', '')
        hot_key = file_name + Config.get('sign_key')
        check_str = Tool.getmd5(hot_key)
        if sign != check_str:
            self.finish(Tool.jsonal(
                {'error': "Sign is error", 'rc': ErrorCode.ERRCODE_BIZ}))
        else:
            file_path = Config.get('dir_playbook') + file_name
            if os.path.isfile(file_path):
                Tool.LOGGER.info("parse from file: " + file_path)
                var = self.parse_vars(file_path)
                self.finish({'vars': var})
            else:
                self.finish(Tool.jsonal(
                    {'error': "No such file in script path", 'rc': ErrorCode.ERRCODE_SYS}))

    def parse_vars(self, file_path):
        contents = FileReadWrite.read_file(file_path)
        env = Environment()
        ignore_vars = []
        yamlstream = yaml.load(contents)
        for yamlitem in yamlstream:
            if isinstance(yamlitem, dict) and yamlitem.get('vars_files', []) and len(yamlitem['vars_files']) > 0:
                for vf in yamlitem['vars_files']:
                    tmp_file = Config.get('dir_playbook') + vf
                    if os.path.isfile(tmp_file):
                        with open(tmp_file, 'r') as fc:
                            tmp_vars = yaml.load(fc)
                            if isinstance(tmp_vars, dict):
                                ignore_vars += tmp_vars.keys()
        if len(ignore_vars) > 0:
            Tool.LOGGER.info("skip vars: " + ",".join(ignore_vars))
        ast = env.parse(contents)
        var = list(meta.find_undeclared_variables(ast))
        var = list(set(var).difference(set(ignore_vars)))
        return var
