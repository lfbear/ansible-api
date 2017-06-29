#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_api.tool import Tool
from ansible.plugins.callback import CallbackBase
from ansible_api.websocket import message
from ansible.executor.task_result import TaskResult as TypeTaskResult
from ansible.executor.stats import AggregateStats as TypeAggregateStats
from ansible.playbook.task import Task as TypeTask
from ansible.playbook.play import Play as TypePlay


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'webscocket'
    CALLBACK_NEEDS_WHITELIST = True

    RC_SUCC = 0
    RC_FAIL = 1

    ITEM_STATUS = ('failed', 'changed', 'skipped', 'unreachable', 'ok')

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.current_taskname = ''
        self.std_lines = dict()

    def reset_output(self):
        self.std_lines.clear()

    def v2_on_any(self, *args, **kwargs):

        wsmsg = dict(
            msg=dict(), rc=self.RC_SUCC,
            task_name=self.current_taskname,
        )

        for crucial in args:
            if isinstance(crucial, TypeTaskResult):
                item = self._fill_item_from_taskresult(
                    init_data=dict(
                        host=crucial._host.get_name(),
                        task_name=crucial._task.get_name(),
                        rc=self.RC_SUCC
                    ), detail=crucial._result)

                if self.std_lines.get(item['host']) == None:
                    self.std_lines[item['host']] = []

                self.std_lines[item['host']].append(item)
                wsmsg['rc'] = item['rc']
                wsmsg['msg'] = item
                message.sendmsg(wsmsg, message.MSGTYPE_INFO)
            elif isinstance(crucial, TypeTask):
                pass
            elif isinstance(crucial, TypePlay):
                pass
                # print(crucial)
            elif isinstance(crucial, TypeAggregateStats):
                hosts = sorted(crucial.processed.keys())
                wsmsg = dict(
                    rc=self.RC_SUCC,
                    task_name=self.current_taskname,
                    msg=dict(kind='play_summarize', list=dict())
                )
                for h in hosts:
                    t = crucial.summarize(h)
                    c = 1 if t['unreachable'] or t['failures'] else 0
                    wsmsg['msg']['list'][h] = dict(
                        host=h, rc=c, unreachable=t[
                            'unreachable'], skipped=t['skipped'],
                        ok=t['ok'], changed=t[
                            'changed'], failures=t['failures']
                    )
                    wsmsg['rc'] += c
                message.sendmsg(wsmsg, message.MSGTYPE_NOTICE)
            elif isinstance(crucial, unicode) or isinstance(crucial, str):
                wsmsg = dict(
                    rc=self.RC_SUCC,
                    task_name=self.current_taskname,
                    msg=dict(kind='desc', unique=crucial)
                )
                message.sendmsg(wsmsg, message.MSGTYPE_NOTICE)
            else:
                Tool.LOGGER.warning(
                    'Found a new type in result [%s]' % (type(crucial)))

    def _fill_item_from_taskresult(self, init_data, detail):
        item = dict()
        if isinstance(init_data, dict):
            item = init_data

        if detail.get('rc'):
            item['rc'] = detail['rc']

        for s in self.ITEM_STATUS:
            if detail.get(s):
                item[s] = detail[s]
                if s in ('failed', 'unreachable'):
                    item['rc'] = self.RC_FAIL

        if detail.get('stdout') and detail['stdout'] != '':
            item['stdout'] = detail['stdout']

        if detail.get('stderr') and detail['stderr'] != '':
            item['stderr'] = detail['stderr']

        if detail.get('msg') and detail['msg'] != '':
            item['msg'] = detail['msg']

        if detail.get('invocation') and detail['invocation'].get('module_args') and detail['invocation']['module_args'].get('_raw_params'):
            item['cmd'] = detail['invocation'][
                'module_args']['_raw_params']
        return item

    ########## special actions on other callback event ##########

    def v2_playbook_on_task_start(self, task, is_conditional):
        wsmsg = dict(
            rc=self.RC_SUCC,
            task_name=self.current_taskname,
            msg=dict(kind='task_start', value=task.get_name())
        )
        message.sendmsg(wsmsg, message.MSGTYPE_NOTICE)

    def v2_playbook_on_play_start(self, play):
        palyname = play.get_name().strip()
        task = list()
        host = list()
        for t in play.get_tasks():
            tmp = [i.get_name() for i in t]
            task = list(set(task + tmp))
        for h_str in play._attributes.get('hosts'):
            h = h_str.split(',')
            host = list(set(host + h))

        self.current_taskname = palyname
        wsmsg = dict(
            rc=self.RC_SUCC,
            task_name=palyname,
            task_list = task,
            host_list = host,
            msg=dict(kind='play_start', value=palyname)
        )
        message.sendmsg(wsmsg, message.MSGTYPE_NOTICE)
        self.reset_output()

    #--- maybe those callback function following will help you ---#

    # def v2_playbook_on_start(self, playbook):
    #     print('PlayBook [%s] start' % playbook._file_name)
    #
    # def v2_runner_retry(self, result):
    #     print("FAILED - RETRYING: %s (%d retries left)." % (result._task, result._result['retries'] - result._result['attempts']))
    #
    # def v2_runner_on_ok(self, result):
    #     pass
    #
    # def v2_runner_on_failed(self, result, ignore_errors):
    #     pass
    #
    # def v2_playbook_on_stats(self, stats):
    #     pass
    #
    # def v2_playbook_on_no_hosts_recrucialing(result):
    #     pass
    #
    # def v2_runner_on_unreachable(self, *args, **kwargs):
    #     pass

    # def defalut_cb(self, *args, **kwargs):
    #     pass
    # v2_runner_on_skipped = defalut_cb
    # v2_runner_on_no_hosts = defalut_cb
    # v2_runner_on_async_poll = defalut_cb
    # v2_runner_on_async_ok = defalut_cb
    # v2_runner_on_async_failed = defalut_cb
    # v2_runner_on_file_diff = defalut_cb
    # v2_playbook_on_notify = defalut_cb
    # v2_playbook_on_no_hosts_matched = defalut_cb
    # v2_playbook_on_cleanup_task_start = defalut_cb
    # v2_playbook_on_handler_task_start = defalut_cb
    # v2_runner_item_on_ok = defalut_cb
    # v2_runner_item_on_failed = defalut_cb
    # v2_runner_item_on_skipped = defalut_cb
    # v2_runner_retry = defalut_cb
