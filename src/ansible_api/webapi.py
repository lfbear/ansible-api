#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from tornado import ioloop, web, httpserver
import threading

from ansible_api.config import Config
from ansible_api import controller
from ansible_api import websocket

class WebApi(object):
    def __init__(self):
        self.application = web.Application([
            (r'/', controller.Main),
            (r'/command', controller.Command),
            (r'/playbook', controller.Playbook),
            (r'/parsevars', controller.ParseVarsFromFile),
            (r'/filelist', controller.FileList),
            (r'/fileitem', controller.FileReadWrite),
            (r'/filexist', controller.FileExist),
            (r'/message', websocket.message),
        ])

        self.http_server = httpserver.HTTPServer(self.application)
        self.http_server.listen(Config.Get('port'), Config.Get('host'))
        self.ioLoop = threading.Thread(target = ioloop.IOLoop.instance().start)

    def start(self):
        self.ioLoop.start()
