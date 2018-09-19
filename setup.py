#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible by tornado
# Base on ansible 2.x (>2.6)
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from setuptools.command.install import install
from setuptools import setup, find_packages
from distutils.version import LooseVersion
import os
import sys

sys.path.insert(0, os.path.abspath('src'))
from ansible_api import __version__


# do something after install
class CustomInstall(install):

    _configfiles = [('/etc/ansible/', ['data/api.cfg'])]
    _pluginfiles = [('plugins/connection', ['data/multipoller.py'])]

    def run(self):
        path = os.path.dirname(ansible.__file__)
        if LooseVersion(ansible.__version__) > LooseVersion('2.0.0'):
            install.run(self)
            self.init_plugin_file(path)
            self.init_config_file()
            print("\033[1;37mAnsible-api v%s install complete.\033[0m" %
                  __version__)
        else:
            print("Error: ansible version " + ansible.__version__ + " < 2.0.0")

    def init_config_file(self):
        for p in self._configfiles:
            path = p[0]
            for f in p[1]:
                file = os.path.join(path, os.path.basename(f))
                if not os.path.isfile(file):
                    os.system(' '.join(['cp', f, file]))
                    print(
                        "\033[1;36mConfiguration file: %s has been copied\033[0m" % file)
                else:
                    print(
                        "\033[4;37mConfiguration file exists: %s\033[0m" % file)

    def init_plugin_file(self, ansible_path):
        for p in self._pluginfiles:
            path = p[0]
            if path[0:1] != '/':
                path = os.path.join(ansible_path, path)
            for f in p[1]:
                file = os.path.join(path, os.path.basename(f))
                os.system(' '.join(['cp', f, file]))
                print("Plugin file: %s copy successfully" % file)

try:
    import ansible
    setup(
        name='ansible-api',
        version=__version__,
        scripts=['bin/ansible-api'],
        package_dir={'': 'src'},
        packages=find_packages('src'),
        install_requires=['tornado==5.1', 'ansible==2.6.4', 'futures'],
        cmdclass={'install': CustomInstall},

        author="lfbear",
        author_email="lfbear@gmail.com",
        description="A restful HTTP API for ansible 2.x by tornado",
        license="GPLv3",
        url="https://github.com/lfbear/ansible-api"
    )

except ImportError:
    print("Error: I can NOT work without ansible")
