#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from tornado import websocket
import json
import time
import os


class message(websocket.WebSocketHandler):
    DEFAULT_CHANNEL = 999

    MSGTYPE_SYS = 1
    MSGTYPE_WARNING = 2
    MSGTYPE_NOTICE = 3
    MSGTYPE_USER = 9

    pool = []

    def check_origin(self, origin):
        return True

    def open(self):
        message.pool.append(self)
        print("[ws_online] current: %d" % len(message.pool))

    def on_message(self, msg):
        json_data = json.loads(msg)
        if isinstance(json_data, dict):
            if json_data.get('instruct', '') == 'ping':
                self.write_message({'type': self.MSGTYPE_SYS, 'msg': 'pong'})
        else:
            self.write_message(
                {'type': self.MSGTYPE_USER, 'msg': u"You said: %s" % msg})

        #print("[ws-send] %s" % msg)

    def on_close(self):
        message.pool.remove(self)
        print("[ws_offline] current: %d" % len(message.pool))

    @classmethod
    def syslog(self, msg):
        if msg.get('type', 0) == 0:
            msg['type'] = self.MSGTYPE_NOTICE
        msg['ctime'] = time.strftime('%m-%d %H:%M:%S', time.localtime())
        print("[rt_log] %s" % msg)
        for item in self.pool:
            item.write_message(msg)
