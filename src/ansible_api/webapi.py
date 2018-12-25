#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible and ansible-runner
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from tornado import ioloop, web, httpserver
from tornado.platform.asyncio import AnyThreadEventLoopPolicy

import asyncio      # Event loop policy that allows loop creation on any thread. tornado >= 5.0
asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

import json
from .tool import Tool
from .config import Config
from . import controller
from . import websocket


class WebApi(object):

    def __init__(self):
        application = web.Application([
            (r'/', controller.Main),
            (r'/asynctest', controller.AsyncTest),
            (r'/command', controller.Command),
            (r'/playbook', controller.Playbook),
            (r'/parsevars', controller.ParseVarsFromFile),
            (r'/filelist', controller.FileList),
            (r'/fileitem', controller.FileReadWrite),
            (r'/filexist', controller.FileExist),
            (r'/message', websocket.Message),
        ])

        http_server = httpserver.HTTPServer(application)
        http_server.listen(Config.get('port'), Config.get('host'))
        config = Config().__dict__
        config['sign_key'] = len(config['sign_key']) * '*'  # mask signature key
        Tool.LOGGER.debug("Config at start: %s" % json.dumps(config))

    def start(self):
        ioloop.IOLoop.instance().start()
