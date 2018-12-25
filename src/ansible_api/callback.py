#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible-runner
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from .websocket import Message
from .report import Reporter


class CallBack(object):

    def __init__(self):
        self._result = []
        self._drawer = []

    def event_handler(self, data):
        rpt = Reporter(data)
        fmt = rpt.tidy()
        detail = rpt.detail()
        if fmt:
            Message.send(fmt)
        if detail:
            self._result.append(detail)

    def get_summary(self):
        result = {}
        for item in self._result:
            k = item.get('host', 'unknown')
            # print(k, item)
            if result.get(k, None) is None:
                result[k] = []
            result[k].append(item)

        return result

    def get_event(self):
        return self._result

    def status_drawer(self, data):
        self._drawer.append(data)

    def status_handler(self, data):
        for item in self._drawer:
            if item.get('status', None) == data:
                before = item.get('before', lambda: {})
                after = item.get('after', lambda: {})
                # print('====>', before(), after())
                rpt = Reporter(before())
                fmt = rpt.simulate(after())
                detail = rpt.detail()
                if fmt:
                    Message.send(fmt)
                if detail:
                    self._result.append(detail)
        # print(data, "status")
