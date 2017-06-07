#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_api.tool import Tool
from tornado import websocket
import json
import time
import os


class message(websocket.WebSocketHandler):

    MSGTYPE_SYS = 1
    MSGTYPE_PANIC = 2
    MSGTYPE_ERROR = 3
    MSGTYPE_WARNING = 4
    MSGTYPE_NOTICE = 5
    MSGTYPE_INFO = 6
    MSGTYPE_USER = 9

    DEFAULT_POOL = []
    SBU_POOL = {}

    def check_origin(self, origin):
        return True

    def select_subprotocol(self, subprotocols):
        sub_str = ''
        if len(subprotocols):
            sub_str = ''.join(subprotocols)
            for p in subprotocols:
                if p == '':
                    continue
                if len(message.SBU_POOL.get(p, [])) == 0:
                    message.SBU_POOL[p] = []
                message.SBU_POOL[p].append(self)
                Tool.LOGGER.debug("online@%s, current: %d" %
                                  (p, len(message.SBU_POOL[p])))

        return sub_str

    def open(self):
        if self.request.headers.get("Sec-WebSocket-Protocol") == None:
            message.DEFAULT_POOL.append(self)
            Tool.LOGGER.debug("online@DEFAULT, current: %d" %
                              len(message.DEFAULT_POOL))

    def on_message(self, msg):
        json_data = json.loads(msg)
        if isinstance(json_data, dict):
            if json_data.get('instruct', '') == 'ping':
                self.write_message({'type': self.MSGTYPE_SYS, 'msg': 'pong'})
        else:
            self.write_message(
                {'type': self.MSGTYPE_USER, 'msg': u"You said: %s" % msg})

        #Tool.LOGGER.debug("[ws-send] %s" % msg)

    def on_close(self):
        if self in message.DEFAULT_POOL:
            message.DEFAULT_POOL.remove(self)
            Tool.LOGGER.debug("offline@DEFAULT, current: %d" %
                              len(message.DEFAULT_POOL))

        for k in message.SBU_POOL:
            if len(message.SBU_POOL[k]) and self in message.SBU_POOL[k]:
                message.SBU_POOL[k].remove(self)
                Tool.LOGGER.debug("offline@%s, current: %d" %
                                  (k, len(message.SBU_POOL[k])))

    @classmethod
    def sendmsg(self, msg, type):
        msgid = msg.get('task_name', '').split('@', 1)
        if len(msgid) == 2:
            task_name, msg_pool = msgid
        else:
            task_name = msgid[0]
            msg_pool = '#DEAULT#'
        task_info = task_name.split('#', 1)
        if len(task_info) == 2:
            msg['task_name'], msg['task_id'] = task_info
        else:
            msg['task_name'] = task_info[0]
            msg['task_id'] = '#'

        msg['type'] = type
        msg['ctime'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        if msg['rc'] == 0:
            if msg.get('type') == message.MSGTYPE_INFO:
                info = "%s\t%s\t%s\t%s\tOK" % (msg_pool, msg.get('task_name'), msg.get('task_id'), msg.get('msg').get('host'))
            elif msg.get('type') == message.MSGTYPE_NOTICE:
                info = "%s\t%s\t%s\t%s\t%s" % (msg_pool, msg.get('task_name'), msg.get('task_id'), msg.get('msg').get('kind'), msg.get('msg').get('value'))
            else:
                info = "%s\t%s" % (msg_pool, msg)
            Tool.LOGGER.info("ANSIBLE_DETAIL\t%s" % info)
        else:
            Tool.LOGGER.warning("ANSIBLE_DETAIL\t%s\t\033[0;33m%s\033[0m" % (msg_pool, msg))
        Tool.LOGGER.debug("\033[0;30m[%s@websocket] %s\033[0m" % (msg_pool, msg))
        
        target = []
        if msg_pool == '#DEAULT#':
            target = self.DEFAULT_POOL
        elif len(self.SBU_POOL.get(msg_pool, [])):
            target = self.SBU_POOL[msg_pool]

        for item in target:
            item.write_message(msg)
