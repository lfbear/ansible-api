#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible and ansible-runner
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class Reporter(object):
    """
    Reporter's life cycle in a callback function
    A ``Reporter`` instance must deal with only one callback message
    """
    EVENT_TYPES = [
        'playbook_on_play_start',
        'playbook_on_task_start',
        'playbook_on_stats',
        'runner_on_ok'
    ]

    def __init__(self, raw):
        self._raw = raw
        self._detail = None

    def tidy(self):
        if self._raw.get('event', None) in Reporter.EVENT_TYPES:
            result = dict()
            result['runner_ident'] = self._raw.get('runner_ident', '')
            result['event'] = self._raw.get('event')
            result['uuid'] = self._raw.get('uuid', '')
            event_data = self._raw.get('event_data', {})
            result['pid'] = event_data.get('pid')

            if result['event'] == 'playbook_on_play_start':
                result['type'] = 'play_start'
                result['name'] = event_data.get('name')
                result['host_list'] = event_data.get('pattern').split(',')
                result['task_list'] = []
                result['parent_uuid'] = event_data.get('playbook_uuid')
            elif result['event'] == 'playbook_on_task_start':
                result['type'] = 'task_start'
                result['name'] = event_data.get('name')
                result['parent_uuid'] = event_data.get('play_uuid')
                result['task_action'] = event_data.get('task_action')
            elif result['event'] == 'playbook_on_stats':
                result['type'] = 'play_stats'
                result['name'] = 'stat'
                result['changed'] = event_data.get('changed')
                result['failures'] = event_data.get('failures')
                result['ok'] = event_data.get('ok')
                result['processed'] = event_data.get('processed')
                result['skipped'] = event_data.get('skipped')
                result['dark'] = event_data.get('dark')
            elif result['event'] == 'runner_on_ok':
                result['type'] = 'task_run'
                result['name'] = event_data.get('task')
                result['host'] = event_data.get('remote_addr')
                result['task_action'] = event_data.get('task_action')
                result['res'] = event_data.get('res')
                result['rc'] = event_data.get('res', {}).get('rc')
                if 'stderr' in event_data.get('res', {}):
                    result['stderr'] = event_data.get('res', {}).get('stderr')
                if 'stdout' in event_data.get('res', {}):
                    result['stdout'] = event_data.get('res', {}).get('stdout')
                self._detail = result
            return result
        else:
            return False

    def simulate(self, data):
        if isinstance(self._raw, dict):
            raw = self.tidy()
            if isinstance(data, dict):
                merge = raw.copy()
                merge.update(data)
                return merge
            else:
                return raw
        else:
            return {}

    def detail(self):
        if self._detail is not None:
            # print('---->', self._detail)
            detail = self._detail.copy()
            options = ['cmd', 'changed', 'failures', 'ok', 'skipped']
            for o in options:
                if o in detail['res']:
                    detail[o] = detail['res'][o]

            detail['task_name'] = detail['name']
            del detail['res'], detail['event'], detail['type'], detail['task_action']
            return detail
