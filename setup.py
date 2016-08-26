#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from setuptools.command.install import install
from setuptools import setup, find_packages
from distutils.version import LooseVersion
import os
import sys

sys.path.insert(0, os.path.abspath('src'))
from ansible_api import __version__


# do something before install
class CustomInstall(install):
    # files that will be modified
    _files = ['executor/task_queue_manager.py', 'plugins/strategy/__init__.py']
    _replace = [
        {
            'search': '_connection_lockfile = ',
            'fill': ' ' * 8 + 'self._prst = [] # all information in processes'
        },
        {
            'search': 'self._final_q.get',
            'fill': ' ' * 16 + 'self._tqm._prst.append(result)'},
    ]
    _configfiles = [('/etc/ansible/', ['data/api.cfg'])]

    def run(self):
        path = os.path.dirname(ansible.__file__)
        if LooseVersion(ansible.__version__) > LooseVersion('2.0.0'):
            # check the file modified in ansible
            cp = self.check_file(path)
            if cp > 0:
                print("those files will be modified to adapt ansible-api")
                self.replace_in_file(path)
            else:
                print("files has already be modified to adapt ansible-api")
            install.run(self)
            self.init_config_file()
        else:
            print("Error: ansible version " + ansible.__version__ + " < 2.0.0")

    def check_file(self, path):
        point = 0
        for f in self._files:
            file = os.path.join(path, f)
            if os.system(' '.join(['grep', "'_prst'", file])) != 0:
                point += 1
        return point

    def replace_in_file(self, path):
        for i, f in enumerate(self._files):
            file = os.path.join(path, f)
            # backup original file
            os.system(' '.join(['cp', file, file + '.ori']))
            os.system(' '.join(['sed', '-i', '"/' + self._replace[i]
                                ['search'] + '/a\\' + self._replace[i]['fill'] + '"', file]))
            print("file: " + file +
                  " has been modified, original file renamed to " + file + '.ori')

    def init_config_file(self):
        for p in self._configfiles:
            path = p[0]
            for f in p[1]:
                file = os.path.join(path, os.path.basename(f))
                if not os.path.isfile(file):
                    os.system(' '.join(['cp', f, file]))
                    print("\033[1;35mConfiguration file: " +
                          file + " has been copied\033[0m")
try:
    import ansible
    setup(
        name='ansible-api',
        version=__version__,
        scripts=['bin/ansible-api'],
        package_dir={'': 'src'},
        packages=find_packages('src'),
        install_requires=['tornado>=4.3', 'ansible>=2.0.0'],
        cmdclass={'install': CustomInstall},

        author="lfbear",
        author_email="lfbear@gmail.com",
        description="A restful HTTP API for ansible 2.x by tornado",
        license="GPLv3",
        url="https://github.com/lfbear/ansible-api"
    )

except ImportError:
    print("Error: I can NOT work without ansible")
