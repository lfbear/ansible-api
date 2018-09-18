#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from collections import namedtuple

from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.parsing.splitter import parse_kv
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.parsing.yaml.objects import AnsibleSequence
from ansible_api.callback import CallbackModule


# new DataLoader for renaming playbook's name
class DataLoaderV2(DataLoader):

    def __init__(self, play_name):
        super(DataLoaderV2, self).__init__()
        self._play_name = play_name

    def load_from_file(self, file_name, cache=True, unsafe=False):
        result = super(DataLoaderV2, self).load_from_file(file_name, cache=True, unsafe=False)
        if isinstance(result, AnsibleSequence):
            for item in result:
                item['name'] = self._play_name
        return result


# new PlaybookExecutor for adding callback
class PlaybookExecutorV2(PlaybookExecutor):

    def __init__(self, playbooks, inventory, variable_manager, loader, options, passwords):
        super(PlaybookExecutorV2, self).__init__(playbooks, inventory, variable_manager, loader, options, passwords)
        if self._tqm is not None:
            self._tqm._stdout_callback = CallbackModule()


class Api(object):

    @staticmethod
    def run_cmd(name, host_list, module, arg, sudo, forks):
        sources = ','.join(host_list)
        if len(host_list) == 1:
            sources += ','

        # initialize needed objects
        Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'remote_user',
                                         'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
                                         'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity',
                                         'check',
                                         'diff'])
        loader = DataLoader()

        options = Options(connection='ssh', module_path=None, forks=forks,
                          remote_user="ansible", private_key_file=None, ssh_common_args=None, ssh_extra_args=None,
                          sftp_extra_args=None, scp_extra_args=None, become=sudo, become_method='sudo',
                          become_user='root', verbosity=None, check=False, diff=False)

        passwords = dict()

        # create inventory and pass to var manager
        inventory = InventoryManager(loader=loader, sources=sources)
        variable_manager = VariableManager(loader=loader, inventory=inventory)

        check_raw = module in ('command', 'shell', 'script', 'raw')

        # create play with tasks
        play_source = dict(
            name=name,  # likes this "taskname#taskid_123@projectname",
            hosts=host_list,
            gather_facts='no',
            tasks=[dict(action=dict(module=module, args=parse_kv(arg, check_raw=check_raw)))]
        )
        play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                options=options,
                passwords=passwords,
                stdout_callback=CallbackModule(),
            )

            rc = tqm.run(play)
            detail = tqm._stdout_callback.std_lines
        finally:
            if tqm is not None:
                tqm.cleanup()
        return {'rc': rc, 'detail': detail}

    @staticmethod
    def run_play_book(palyname, yml_file, sources, forks):
        # initialize needed objects
        loader = DataLoaderV2(palyname)
        Options = namedtuple('Options', ['listtags', 'listtasks', 'listhosts',
                                         'syntax', 'connection', 'module_path', 'forks', 'remote_user',
                                         'private_key_file', 'ssh_common_args', 'ssh_extra_args',
                                         'sftp_extra_args', 'scp_extra_args', 'become', 'become_method',
                                         'become_user', 'verbosity', 'check'])
        pb_options = Options(listtags=False, listtasks=False,
                             listhosts=False, syntax=False, connection='ssh',
                             module_path=None, forks=forks, remote_user='ansible',
                             private_key_file=None, ssh_common_args=None,
                             ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None,
                             become=True, become_method='sudo', become_user='root',
                             verbosity=None, check=False)

        passwords = {}

        # create inventory and pass to var manager
        inventory = InventoryManager(loader=loader, sources=sources)
        variable_manager = VariableManager(loader=loader, inventory=inventory)

        pbex = PlaybookExecutorV2(playbooks=[yml_file],
                                  inventory=inventory, variable_manager=variable_manager, loader=loader,
                                  options=pb_options, passwords=passwords)
        rc = pbex.run()
        return {'rc': rc, 'detail': pbex._tqm._stdout_callback.std_lines}
