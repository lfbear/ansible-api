#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import time
import json

__all__ = ['Tool']


class Tool(object):
    LOG_REPORT_HANDERL = None
    ERRCODE_NONE = 0
    ERRCODE_SYS = 1
    ERRCODE_BIZ = 2

    @staticmethod
    def getmd5(str):
        import hashlib
        m = hashlib.md5()
        m.update(str.encode('utf-8'))
        return m.hexdigest()

    @staticmethod
    def reporting(str):
        report = time.strftime('%Y-%m-%d %H:%M:%S',
                               time.localtime()) + ' | ' + str
        if Tool.LOG_REPORT_HANDERL:
            Tool.LOG_REPORT_HANDERL.write(report + "\n")
            Tool.LOG_REPORT_HANDERL.flush()
        else:
            print("\033[5;30;47m%s\033[0m" % report)

    @staticmethod
    def jsonal(data):
        return json.dumps(data)

    @staticmethod
    def parsejson(string):
        return json.loads(string.decode('utf-8'))
