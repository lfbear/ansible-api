#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from collections import namedtuple
from collections import MutableMapping
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
#from ansible.plugins.callback.default import CallbackModule
from ansible.parsing.yaml.objects import AnsibleSequence
from ansible_api.callback import CallbackModule
from ansible_api.websocket import message
import tornado.gen

# new DataLoader for renaming playbook's name
class DataLoaderV2(DataLoader):

    def __init__(self, play_name):
        DataLoader.__init__(self)
        self._playname = play_name

    def load_from_file(self, file_name):
        result = DataLoader.load_from_file(self, file_name)
        if isinstance(result, AnsibleSequence):
            for item in result:
                item['name'] = self._playname
        return result

# new PlaybookExecutor for adding callback
class PlaybookExecutorV2(PlaybookExecutor):

    def __init__(self, playbooks, inventory, variable_manager, loader, options, passwords):
        self._playbooks = playbooks
        self._inventory = inventory
        self._variable_manager = variable_manager
        self._loader = loader
        self._options = options
        self.passwords = passwords
        self._unreachable_hosts = dict()

        if options.listhosts or options.listtasks or options.listtags or options.syntax:
            self._tqm = None
        else:
            self._tqm = TaskQueueManager(inventory=inventory, variable_manager=variable_manager,
                                         loader=loader, options=options, passwords=self.passwords, stdout_callback=CallbackModule())


class Api(object):

    @staticmethod
    def runCmd(name, target, module, arg, sudo, forks):
        # initialize needed objects
        variable_manager = VariableManager()
        loader = DataLoader()
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
                             become=sudo, become_method='sudo', become_user='root',
                             verbosity=None, check=False)

        passwords = {}

        # create inventory and pass to var manager
        inventory = Inventory(
            loader=loader, variable_manager=variable_manager)
        variable_manager.set_inventory(inventory)

        # create play with tasks
        play_source = dict(
            name=name,  # likes this "taskname#taskid_123@projectname",
            hosts=target,
            gather_facts='no',
            tasks=[dict(action=dict(module=module, args=arg))]
        )
        play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                options=pb_options,
                passwords=passwords,
                stdout_callback=CallbackModule(),
            )

            # tqm._stdout_callback.reset_output()
            rc = tqm.run(play)
            detail = tqm._stdout_callback.std_lines
            # tqm._stdout_callback.reset_output()
        finally:
            if tqm is not None:
                tqm.cleanup()
        return {'rc': rc, 'detail': detail}

    @staticmethod
    def runPlaybook(palyname, yml_file, myvars, forks):
        # initialize needed objects
        variable_manager = VariableManager()
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
        inventory = Inventory(
            loader=loader, variable_manager=variable_manager)
        variable_manager.set_inventory(inventory)
        variable_manager.extra_vars = myvars
        pbex = PlaybookExecutorV2(playbooks=[yml_file],
                                  inventory=inventory, variable_manager=variable_manager, loader=loader,
                                  options=pb_options, passwords=passwords)
        # pbex._tqm._stdout_callback.reset_output()
        rc = pbex.run()
        return {'rc': rc, 'detail': pbex._tqm._stdout_callback.std_lines}
