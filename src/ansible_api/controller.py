#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible
# Base on ansible-runner and sanic
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear, pgder

import os
import sys
import time
import yaml
import asyncio
import ansible_runner
import concurrent.futures

from jinja2 import Environment, meta
from sanic.views import HTTPMethodView
from sanic.response import json

from .tool import Tool
from .config import Config
from .realtimemsg import RealTimeMessage
from .callback import CallBack
from . import RTM_CHANNEL_DEFAULT

__all__ = [
    'Main',
    'FileList',
    'FileReadWrite',
    'FileExist',
    'ParseVarsFromFile',
    'Command',
    'Playbook',
    'Message',
    'NonBlockTest',
]


class ErrorCode(object):
    ERRCODE_NONE = 0
    ERRCODE_SYS = 1
    ERRCODE_BIZ = 2


class MyHttpView(HTTPMethodView):
    pass


class Main(MyHttpView):

    def get(self, request):
        return json({'message': "Hello, I am Ansible Api", 'rc': ErrorCode.ERRCODE_NONE})


class NonBlockTest(MyHttpView):

    async def get(self, request):
        start = time.time()
        msg = await self.run_block()
        end = time.time() - start
        return json({'message': msg + 'and total cost time: %s' % end, 'rc': ErrorCode.ERRCODE_NONE})

    async def run_block(self):
        await asyncio.sleep(10)
        return 'I have slept 10 s'


class Command(MyHttpView):

    async def post(self, request):
        data = request.json if request.json is not None else {}
        for test in ['n', 'm', 't', 's']:  # required parameter check
            if test not in data:
                return json({'error': "Lack of necessary parameters [%s]" % test,
                             'rc': ErrorCode.ERRCODE_BIZ})

        bad_cmd = ['reboot', 'su', 'sudo', 'dd',
                   'mkfs', 'shutdown', 'half', 'top']
        name = data.get('n').encode('utf-8').decode()
        module = data.get('m')
        arg = data.get('a', '').encode('utf-8').decode()
        target = data.get('t')
        sign = data.get('s')
        # sudo = True if data.get('r') else False # discard
        # forks = data.get('c', 50) # discard
        cmd_info = arg.split(' ', 1)
        Tool.LOGGER.info('run: {0}, {1}, {2}, {3}'.format(
            name, target, module, arg))
        hot_key = name + module + target + Config.get('sign_key')
        check_str = Tool.getmd5(hot_key)
        if sign != check_str:
            return json({'error': "Sign is error", 'rc': ErrorCode.ERRCODE_BIZ})
        else:
            if module in ('shell', 'command') and cmd_info[0] in bad_cmd:
                return json({'error': "This is danger shell: " + cmd_info[0], 'rc': ErrorCode.ERRCODE_BIZ})
            else:
                try:
                    cb = CallBack()
                    cb.status_drawer(dict(status='starting', raw=lambda: dict(
                        task_name=module, event='playbook_on_play_start', runner_ident=name,
                        event_data=dict(pattern=target, name=module)),
                                          after=lambda: dict(task_list=[module])))
                    loop = asyncio.get_running_loop()
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        response = await loop.run_in_executor(pool, self.run, target, name, module, arg, cb)
                        # response = yield self.run(target, name, module, arg, cb)
                        # response = self.run(target, name, module, arg, cb)
                        return json(dict(rc=response.rc, detail=cb.get_summary()))
                except Exception as e:
                    Tool.LOGGER.exception(e)
                    return json({'error': str(e), 'rc': ErrorCode.ERRCODE_BIZ})

    def run(self, target, name, module, arg, cb):
        return ansible_runner.interface.run(
            host_pattern=target, inventory='/etc/ansible/hosts',
            envvars=dict(PATH=os.environ.get('PATH') + ':' + sys.path[0]),
            ident=name, module=module, module_args=arg,
            event_handler=cb.event_handler, status_handler=cb.status_handler
        )


class Playbook(MyHttpView):

    async def post(self, request):
        data = request.json if request.json is not None else {}
        for test in ['n', 'h', 's', 'f']:  # required parameter check
            if test not in data:
                return json({'error': "Lack of necessary parameters [%s]" % test,
                             'rc': ErrorCode.ERRCODE_BIZ})

        name = data['n'].encode('utf-8').decode()
        hosts = data['h']
        sign = data['s']
        yml_file = data['f'].encode('utf-8').decode()
        # forks = data.get('c', 50)
        hot_key = name + hosts + yml_file + Config.get('sign_key')
        check_str = Tool.getmd5(hot_key)
        if sign != check_str:
            return json({'error': "Sign is error", 'rc': ErrorCode.ERRCODE_BIZ})
        else:
            my_vars = {'hosts': hosts}
            # injection vars in playbook (rule: vars start with "v_" in
            # post data)
            for (k, v) in data.items():
                if k[0:2] == "v_":
                    my_vars[k[2:]] = v
            yml_file = Config.get('dir_playbook') + yml_file

            if os.path.isfile(yml_file):
                task_list = []
                with open(yml_file, 'r') as contents:
                    yaml_cnt = yaml.load(contents)
                    if len(yaml_cnt) > 0 and len(yaml_cnt[0].get('tasks', [])) > 0:
                        task_list = [x.get('name', 'unnamed') for x in yaml_cnt[0]['tasks']]
                Tool.LOGGER.info("playbook: {0}, host: {1}".format(yml_file, hosts))
                try:
                    cb = CallBack()
                    cb.event_pepper('playbook_on_play_start', dict(task_list=task_list))
                    loop = asyncio.get_running_loop()
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        response = await loop.run_in_executor(pool, self.run, hosts, name, yml_file, my_vars, cb)
                        # response = yield self.run(hosts, name, yml_file, my_vars, cb)
                        return json(dict(rc=response.rc, detail=cb.get_summary()))
                except BaseException as e:
                    Tool.LOGGER.exception(e)
                    return json({'error': str(e), 'rc': ErrorCode.ERRCODE_BIZ})
            else:
                return json({'error': "yml file(" + yml_file + ") is not existed",
                             'rc': ErrorCode.ERRCODE_SYS})

    def run(self, hosts, name, yml_file, my_vars, cb):
        return ansible_runner.interface.run(
            host_pattern=hosts, inventory='/etc/ansible/hosts',
            envvars=dict(PATH=os.environ.get('PATH') + ':' + sys.path[0]),
            playbook=yml_file, ident=name, extravars=my_vars,
            event_handler=cb.event_handler, status_handler=cb.status_handler
        )


class FileList(MyHttpView):

    async def get(self, request):
        path = request.args.get('type', 'script')
        sign = request.args.get('sign', '')
        allows = ['script', 'playbook']
        if path in allows:
            hot_key = path + Config.get('sign_key')
            check_str = Tool.getmd5(hot_key)
            if sign != check_str:
                return json({'error': "Sign is error", 'rc': ErrorCode.ERRCODE_BIZ})
            else:
                path_var = Config.get('dir_' + path)
                if os.path.exists(path_var):
                    Tool.LOGGER.info("read file list: " + path_var)
                    dirs = os.listdir(path_var)
                    return json({'list': dirs})
                else:
                    return json(
                        {'error': "Path is not existed", 'rc': ErrorCode.ERRCODE_SYS})
        else:
            return json(
                {'error': "Wrong type in argument", 'rc': ErrorCode.ERRCODE_SYS})


class FileReadWrite(MyHttpView):

    async def get(self, request):
        path = request.args.get('type', 'script')
        file_name = request.args.get('name')
        sign = request.args.get('sign', '')
        allows = ['script', 'playbook']
        if path in allows:
            hot_key = path + file_name + Config.get('sign_key')
            check_str = Tool.getmd5(hot_key)
            if sign != check_str:
                self.finish(json(
                    {'error': "Sign is error", 'rc': ErrorCode.ERRCODE_BIZ}))
            else:
                file_path = Config.get('dir_' + path) + file_name
                if os.path.isfile(file_path):
                    contents = self.read_file(file_path)
                    return json({'content': contents})
                else:
                    return json(
                        {'error': "No such file in script path", 'rc': ErrorCode.ERRCODE_BIZ})
        else:
            return json(
                {'error': "Wrong type in argument", 'rc': ErrorCode.ERRCODE_SYS})

    @classmethod
    def read_file(cls, file_path):
        try:
            Tool.LOGGER.info("read from file: " + file_path)
            with open(file_path) as file:
                contents = file.read()
        except BaseException:
            Tool.LOGGER.error("failed in reading from file: " + file_path)
            contents = ''
        return contents

    async def post(self, request):
        data = request.json if request.json is not None else {}
        path = data.get('p', None)
        filename = data.get('f', None)
        content = data.get('c', '').encode('utf-8').decode()
        sign = data.get('s', None)
        if not filename or not content or not sign or path \
                not in ['script', 'playbook']:
            return json(
                {'error': "Lack of necessary parameters", 'rc': ErrorCode.ERRCODE_SYS})
        hot_key = path + filename + Config.get('sign_key')
        check_str = Tool.getmd5(hot_key)
        if sign != check_str:
            return json({'error': "Sign is error", 'rc': ErrorCode.ERRCODE_BIZ})
        else:
            file_path = Config.get('dir_' + path) + filename
            result = self.write_file(file_path, content)
            return json({'ret': result})

    def write_file(self, file_path, content):
        result = True
        try:
            Tool.LOGGER.info("write to file: " + file_path)
            with open(file_path, 'w') as file:
                file.write(content)
        except BaseException as err:
            result = False
            Tool.LOGGER.error("failed in writing to file: " + file_path)

        return result


class FileExist(MyHttpView):

    async def get(self, request):
        path = request.args.get('type', 'script')
        file_name = request.args.get('name')
        sign = request.args.get('sign', '')
        allows = ['script', 'playbook']
        if path in allows:
            hot_key = path + file_name + Config.get('sign_key')
            check_str = Tool.getmd5(hot_key)
            if sign != check_str:
                return json(
                    {'error': "Sign is error", 'rc': ErrorCode.ERRCODE_BIZ})
            else:
                file_path = Config.get('dir_' + path) + file_name
                Tool.LOGGER.info("file exist? " + file_path)
                if os.path.isfile(file_path):
                    return json({'ret': True})
                else:
                    return json({'ret': False})
        else:
            return json(
                {'error': "Wrong type in argument", 'rc': ErrorCode.ERRCODE_SYS})


class ParseVarsFromFile(MyHttpView):

    async def get(self, request):
        file_name = request.args.get('name')
        sign = request.args.get('sign', '')
        hot_key = file_name + Config.get('sign_key')
        check_str = Tool.getmd5(hot_key)
        if sign != check_str:
            return json({'error': "Sign is error", 'rc': ErrorCode.ERRCODE_BIZ})
        else:
            file_path = Config.get('dir_playbook') + file_name
            if os.path.isfile(file_path):
                Tool.LOGGER.info("parse from file: " + file_path)
                var = self.parse_vars(file_path)
                return json({'vars': var})
            else:
                return json({'error': "No such file in script path", 'rc': ErrorCode.ERRCODE_SYS})

    def parse_vars(self, file_path):
        contents = FileReadWrite.read_file(file_path)
        env = Environment()
        ignore_vars = []
        yaml_stream = yaml.load(contents)
        for yaml_item in yaml_stream:
            if isinstance(yaml_item, dict) and yaml_item.get('vars_files', []) and len(yaml_item['vars_files']) > 0:
                for vf in yaml_item['vars_files']:
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


class Message:

    async def websocket(request, ws):
        if ws.subprotocol is None:
            channel = RTM_CHANNEL_DEFAULT
        else:
            channel = ws.subprotocol
        RealTimeMessage.set(channel, ws)
        while True:
            data = await ws.recv()
            msg = 'you say [%s] @%s: ' % (data, channel)
            # print('--- websocket debug ---', msg)
            await ws.send(msg)
