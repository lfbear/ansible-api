#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase
from ansible.executor.task_result import TaskResult
from ansible.playbook.task import Task
from ansible_api.websocket import message


class CallbackModule(CallbackBase):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'webscocket'
    CALLBACK_NEEDS_WHITELIST = True

    RC_SUCC = 0
    RC_FAIL = 1

    current_taskname = ''

    def display(self, result, rc):
        params = {'msg': {}, 'task_name': self.current_taskname,
                  'rc': rc, 'ctime': ''}
        if isinstance(result, TaskResult):
            params['msg']['host'] = result._host.get_name()
            params['msg']['module'] = result._task.get_name()
            detail = result._result
            # print(detail)
            if result.is_changed():
                params['rc'] = self.RC_SUCC
                if detail['invocation'].get('module_name') == 'command':
                    params['msg']['unique'] = {'cost_time': detail['delta']}
                elif detail['invocation'].get('module_name') == 'script':
                    params['msg']['unique'] = {'script_file': detail[
                        'invocation']['module_args']['_raw_params']}
                elif detail.get('state'):
                    params['msg']['unique'] = {'state': detail['state']}
                elif detail.get('cmd'):
                    params['msg']['unique'] = {'cmd': detail['cmd']}
                else:
                    print('Found a new type in TaskResult')
            elif detail.get('msg', '') != '':  # 有msg信息 认为出现了错误
                params['rc'] = self.RC_FAIL
                params['msg']['error'] = detail['msg']
            else:
                params['rc'] = self.RC_SUCC
                print("is_changed=false")
                print(detail)
                #params['msg']['unique'] = {'unknown':detail['msg']}

            message.sendmsg(params, message.MSGTYPE_INFO)

        elif isinstance(result, unicode) or isinstance(result, str):
            params['rc'] = rc
            params['msg']['kind'] = 'desc'
            params['msg']['unique'] = result
            message.sendmsg(params, message.MSGTYPE_NOTICE)
        elif isinstance(result, Task):
            params['rc'] = rc
            params['msg']['kind'] = 'task'
            params['msg']['value'] = result.get_name()
            message.sendmsg(params, message.MSGTYPE_NOTICE)
        else:
            print('Found a new type in result [%s]' % (type(result)))

    def v2_playbook_on_start(self, playbook):
        #message.sendmsg({'rc':self.RC_SUCC,'task_name':'none@null', 'msg': {'kind':'playbook','value':playbook._file_name}},message.MSGTYPE_NOTICE)
        print('PlayBook [%s] start' % playbook._file_name)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.display(task, self.RC_SUCC)

    def v2_playbook_on_play_start(self, play):
        palyname = play.get_name().strip()
        self.current_taskname = palyname
        hosts = play._attributes.get('hosts')[0].split(',')  # why is list[0]
        message.sendmsg({'rc': self.RC_SUCC, 'task_name': self.current_taskname, 'task_count': len(
            hosts), 'msg': {'kind': 'play_start', 'value': palyname}}, message.MSGTYPE_NOTICE)

    def v2_runner_retry(self, result):
        msg = "FAILED - RETRYING: %s (%d retries left)." % (
            result._task, result._result['retries'] - result._result['attempts'])
        message.sendmsg({'rc': self.RC_FAIL, 'task_name': self.current_taskname, 'msg': {
                        'kind': 'needs_retry', 'value': result._task}}, message.MSGTYPE_NOTICE)

    def v2_playbook_on_stats(self, stats):
        #self.display('PLAY SUMMARIZE')

        hosts = sorted(stats.processed.keys())
        details = {}
        return_code = 0
        for h in hosts:
            t = stats.summarize(h)
            rc = 1 if t['unreachable'] or t['failures'] else 0
            details[h] = {'host': h, 'rc': rc, 'unreachable': t['unreachable'], 'skipped': t[
                'skipped'], 'ok': t['ok'], 'changed': t['changed'], 'failures': t['failures']}
            #self.display('Host:%s, Stat:%s'% (h,str(t)),rc)
            return_code += rc
        message.sendmsg({'rc': return_code, 'task_name': self.current_taskname, 'msg': {
                        'kind': 'play_summarize', 'list': details}}, message.MSGTYPE_NOTICE)

    def v2_runner_on_ok(self, result):
        self.display(result, self.RC_SUCC)

    def v2_runner_on_failed(self, result, ignore_errors):
        self.display(result, self.RC_FAIL)

    def v2_playbook_on_no_hosts_remaining(result):
        pass

    v2_runner_on_skipped = display
    v2_runner_on_unreachable = display
    v2_runner_on_no_hosts = display
    v2_runner_on_async_poll = display
    v2_runner_on_async_ok = display
    v2_runner_on_async_failed = display
    v2_runner_on_file_diff = display
    v2_playbook_on_notify = display
    v2_playbook_on_no_hosts_matched = display
    v2_playbook_on_cleanup_task_start = display
    v2_playbook_on_handler_task_start = display
    v2_runner_item_on_ok = display
    v2_runner_item_on_failed = display
    v2_runner_item_on_skipped = display
    v2_runner_retry = display
