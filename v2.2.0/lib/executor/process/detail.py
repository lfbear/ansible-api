#
# Modify version by lfbear <lfbear@gmail.com>
#
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.executor.process.result import ResultProcess
#from ansible.executor.task_result import TaskResult

__all__ = ['DetailProcess']

class DetailProcess():

    def __init__(self, rlist):
        self._detail = { }
        if isinstance(rlist,list):
            for result in rlist:
                if result[0] in ('host_task_ok', 'host_task_failed', 'host_task_skipped', 'host_unreachable'):
                    task_result = result[1]
                    host = task_result._host.name
                    rzt = task_result._result
                    rzt['task_name'] = task_result._task.get_name().format('%s').encode('utf-8')
                    if 'ansible_facts' not in rzt.keys(): # facts data is not we need
                        self._detail.setdefault(host,[]).append(rzt)
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
                    print('-'*5+'DATA SKIPPING'+'-'*5)
                    print(result[0], end="\t")
                    print(result[1])

    def run(self):
        return self._detail
