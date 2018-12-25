#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible and ansible-runner
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type
from .tool import Tool


class Reporter(object):
    """
    Reporter's life cycle in a callback function
    A ``Reporter`` instance must deal with only one callback message
    """

    def __init__(self, raw):
        self._raw = raw
        self._detail = None
        self._after = {}

    def tidy(self):
        if self._raw.get('event', None) is not None:
            result = dict()
            result['runner_ident'] = self._raw.get('runner_ident', '')
            result['event'] = self._raw.get('event')
            result['uuid'] = self._raw.get('uuid', '')
            event_data = self._raw.get('event_data', {})
            result['pid'] = event_data.get('pid')
            if result['event'][:10] == 'runner_on_':
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
            elif result['event'] == 'playbook_on_play_start':
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
            # elif result['event'] == 'MORE EVENT NAME'
            # pass # --- you can add more event filter here ---
            else:
                Tool.LOGGER.warn('Unknown event name: %s' % result['event'])
                return False
            # adorn custom contents
            if result['event'] in self._after:
                result.update(self._after[result['event']])
            return result
        else:
            return False

    def adorn(self, data):
        self._after.update(data)

    def detail(self):
        if self._detail is not None:
            # print('---->', self._detail)
            detail = self._detail.copy()
            options = ['cmd', 'changed', 'failures', 'ok', 'skipped', 'unreachable']
            for o in options:
                if o in detail['res']:
                    detail[o] = detail['res'][o]

            detail['task_name'] = detail['name']
            del detail['res'], detail['event'], detail['type'], detail['task_action']
            return detail
