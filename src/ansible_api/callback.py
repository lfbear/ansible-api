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

    def display(self, result, rc = 0):
        params = { 'msg':{} , 'type': 0, 'ctime':'' }

        if isinstance(result,TaskResult) :
            #print(type(result._task))
            params['msg']['host'] = result._host.get_name()
            params['msg']['task'] = result._task.get_name()
            detail = result._result

            if result.is_changed():
                params['msg']['rc'] = 0;
                if detail['invocation']['module_name'] == 'command' :
                    params['msg']['one'] = 'cost time: %s s' % (detail['delta'])
                elif detail['invocation']['module_name'] == 'script' :
                    params['msg']['one'] = 'remote script ready: %s' % (detail['invocation']['module_args']['_raw_params'])
                else :
                    pass
            else:
                params['msg']['rc'] = 1;
                params['msg']['one'] = detail['msg'];
            params['msg']['one'] = '%s [%s] ' % (result._host.get_name(),result._task.get_name()) + params['msg']['one']

        elif isinstance(result,unicode) or isinstance(result,str):
            params['msg']['rc'] = rc;
            params['msg']['one'] = result;
        elif isinstance(result,Task):
            params['msg']['rc'] = rc;
            params['msg']['one'] = 'TASK [%s]' % (result.get_name())
        else:
            params['msg']['rc'] = 9;
            params['msg']['one'] = 'UNKNOWN FORMAT [%s]' % type(result)

        message.syslog(params)

    def v2_playbook_on_start(self, playbook):
        self.display('PLAYBOOK [%s]' % playbook._file_name)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.display(task)

    def v2_playbook_on_play_start(self, play):
        name = play.get_name().strip()
        if not name:
            msg = "PLAY"
        else:
            msg = "PLAY [%s]" % name
        message.syslog({'msg':{'one':msg, 'rc':0}, 'type':2})

    def v2_runner_retry(self, result):
        msg = "FAILED - RETRYING: %s (%d retries left)." % (result._task, result._result['retries'] - result._result['attempts'])
        self.display(msg)

    def v2_playbook_on_stats(self, stats):
        self.display('PLAY SUMMARIZE')

        hosts = sorted(stats.processed.keys())

        for h in hosts:
            t = stats.summarize(h)
            rc = 1 if t['unreachable'] or t['failures'] else 0
            self.display('Host:%s, Stat:%s'% (h,str(t)),rc)

    v2_runner_on_ok = display
    v2_runner_on_failed = display
    v2_runner_on_skipped = display
    v2_runner_on_unreachable = display
    v2_runner_on_no_hosts = display
    v2_runner_on_async_poll = display
    v2_runner_on_async_ok = display
    v2_runner_on_async_failed = display
    v2_runner_on_file_diff = display
    v2_playbook_on_notify = display
    v2_playbook_on_no_hosts_matched = display
    v2_playbook_on_no_hosts_remaining = display
    v2_playbook_on_cleanup_task_start = display
    v2_playbook_on_handler_task_start = display
    v2_runner_item_on_ok = display
    v2_runner_item_on_failed = display
    v2_runner_item_on_skipped = display
    v2_runner_retry = display
