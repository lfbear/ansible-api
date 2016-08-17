#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear
# Version: 0.1.1 at 2016.8.17

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

__all__ = ['DetailProcess']


class DetailProcess():

    def __init__(self, rlist):
        self._detail = {}
        if isinstance(rlist, list):
            for result in rlist:
                if result[0] in ('host_task_ok', 'host_task_failed', 'host_task_skipped', 'host_unreachable'):
                    task_result = result[1]
                    host = task_result._host.name
                    rzt = task_result._result
                    rzt['task_name'] = task_result._task.get_name().format(
                        '%s').encode('utf-8')
                    if 'ansible_facts' not in rzt.keys():  # facts data is not we need
                        self._detail.setdefault(host, []).append(rzt)
                    #         if result[0] == 'host_task_failed' or task_result.is_failed():
                    #         elif result[0] == 'host_unreachable':
                    #         elif result[0] == 'host_task_skipped':
                    #         elif result[0] == 'host_task_ok':
                    #     elif result[0] == 'add_host':
                    #     elif result[0] == 'add_group':
                    #     elif result[0] == 'notify_handler':
                    #     elif result[0] == 'register_host_var':
                    #     elif result[0] in ('set_host_var', 'set_host_facts'):
                    #
                    #     else:
                    #
                else:
                    print('-' * 5 + 'DATA SKIPPING' + '-' * 5)
                    print(result[0], end="\t")
                    print(result[1])

    def run(self):
        return self._detail
