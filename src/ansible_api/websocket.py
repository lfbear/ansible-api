#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible and ansible-runner
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear, pgder

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import json
import time
from .tool import Tool
from tornado import websocket


class Message(websocket.WebSocketHandler):
    MSGTYPE_SYS = 1
    MSGTYPE_PANIC = 2
    MSGTYPE_ERROR = 3
    MSGTYPE_WARNING = 4
    MSGTYPE_NOTICE = 5
    MSGTYPE_INFO = 6
    MSGTYPE_USER = 9

    DEFAULT_POOL = []
    SUB_POOL = {}

    def check_origin(self, origin):
        return True

    def select_subprotocol(self, subprotocols):
        selected = None
        if len(subprotocols):
            selected = subprotocols[0]
            for p in subprotocols:
                if p == '':
                    continue
                if len(Message.SUB_POOL.get(p, [])) == 0:
                    Message.SUB_POOL[p] = []
                Message.SUB_POOL[p].append(self)
                Tool.LOGGER.debug("online@%s, current: %d" %
                                  (p, len(Message.SUB_POOL[p])))

        return selected

    def open(self):
        if self.request.headers.get("Sec-WebSocket-Protocol") is None:
            Message.DEFAULT_POOL.append(self)
            Tool.LOGGER.debug("online@DEFAULT, current: %d" %
                              len(Message.DEFAULT_POOL))

    def on_message(self, msg):
        json_data = json.loads(msg)
        if isinstance(json_data, dict):
            if json_data.get('instruct', '') == 'ping':
                self.write_message({'type': self.MSGTYPE_SYS, 'msg': 'pong'})
        else:
            self.write_message(
                {'type': self.MSGTYPE_USER, 'msg': u"You said: %s" % msg})
        # Tool.LOGGER.debug("[ws-send] %s" % msg)

    def on_close(self):
        if self in Message.DEFAULT_POOL:
            Message.DEFAULT_POOL.remove(self)
            Tool.LOGGER.debug("offline@DEFAULT, current: %d" %
                              len(Message.DEFAULT_POOL))

        for k in Message.SUB_POOL:
            if len(Message.SUB_POOL[k]) and self in Message.SUB_POOL[k]:
                Message.SUB_POOL[k].remove(self)
                Tool.LOGGER.debug("offline@%s, current: %d" %
                                  (k, len(Message.SUB_POOL[k])))

    @classmethod
    def send(cls, data):
        msg = dict()
        msgid = data.get('runner_ident', '').split('@', 1)
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

        msg['type'] = Message.MSGTYPE_INFO if data['type'] == 'task_run' else Message.MSGTYPE_NOTICE
        msg['ctime'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        if msg.get('type') == Message.MSGTYPE_INFO:
            msg['msg'] = dict(host=data['host'], task_name=data['name'], rc=data['rc'])
            options = ['stdout', 'stderr', 'cmd', 'changed', 'start', 'delta']
            for f in options:
                if f in data['res']:
                    msg['msg'][f] = data['res'][f]
            msg['rc'] = data['rc']
            # info = "%s\t%s\t%s\t%s\tOK" % (
            # msg_pool, msg.get('task_name'), msg.get('task_id'), msg.get('msg').get('host'))
            if msg['rc'] != 0:
                Tool.LOGGER.warning("ERROR DETAIL: %s\t%s" % (msg_pool, msg))
        else:
            options = ['host_list', 'task_list', 'changed', 'failures', 'ok', 'skipped']
            for f in options:
                if f in data:
                    msg[f] = data[f]
            msg['msg'] = dict(kind=data['type'], value=data['name'])
            # info = "%s\t%s\t%s\t%s\t%s" % (
            # msg_pool, msg.get('task_name'), msg.get('task_id'), msg.get('msg').get('kind'),
            # msg.get('msg').get('value'))
        Tool.LOGGER.debug("[%s@websocket] %s" % (msg_pool, msg))

        target = []
        if msg_pool == '#DEAULT#':
            target = cls.DEFAULT_POOL
        elif len(cls.SUB_POOL.get(msg_pool, [])):
            target = cls.SUB_POOL[msg_pool]

        for item in target:
            item.write_message(msg)
