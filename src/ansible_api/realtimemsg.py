#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible
# Base on ansible-runner and sanic
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

import json
from .report import Reporter
from .tool import Tool


class RealTimeMessage:
    UserList = {}

    @staticmethod
    def set(group, handler):
        if group not in RealTimeMessage.UserList:
            RealTimeMessage.UserList[group] = []

        RealTimeMessage.UserList[group].append(handler)
        Tool.LOGGER.debug('new connection from WebSocket [%s]' % group)
        return True

    @staticmethod
    def get(group):
        if group in RealTimeMessage.UserList:
            return RealTimeMessage.UserList[group]
        else:
            return []

    @staticmethod
    async def send(data):
        group, msg = Reporter.fmt_realtime(data)
        Tool.LOGGER.debug('[%s@websocket] %s' % (group, msg))
        if group in RealTimeMessage.UserList:
            for ws in RealTimeMessage.UserList.get(group, []):
                if ws.open:
                    try:
                        await ws.send(json.dumps(msg))
                    # FOR websockets.exceptions.ConnectionClosed: WebSocket connection is closed: code = 1006
                    except BaseException as e:
                        Tool.LOGGER.exception(e)
                else:
                    # WSUser.UserList = [u for u in WSUser.UserList if u != x]
                    RealTimeMessage.UserList.get(group).remove(ws)
