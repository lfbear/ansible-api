#!/usr/bin/env python
# coding: utf-8

# A restful HTTP API for ansible
# Base on ansible-runner and sanic
# Github <https://github.com/lfbear/ansible-api>
# Author: lfbear

from setuptools.command.install import install
from setuptools import setup, find_packages
from distutils.version import LooseVersion
import os
import sys
import pkg_resources

sys.path.insert(0, os.path.abspath('src'))
from ansible_api import __version__

ABSIBLE_REQUIRE = '2.6.0'
ABSIBLER_REQUIRE = '1.2.0'
SANIC_REQUIRE = '0.8.0'
PYTHON_REQUIRE = '3.7'


# do something after install
class CustomInstall(install):
    _configfiles = [('/etc/ansible/', ['data/api.cfg'])]

    def run(self):
        cur_python_ver = "%d.%d" % (sys.version_info[0], sys.version_info[1])
        if LooseVersion(cur_python_ver) < LooseVersion(PYTHON_REQUIRE):
            print("Error: Python version " + cur_python_ver + " < " + PYTHON_REQUIRE)
            return False
        os.system("%s -m pip install ansible>=%s" % (sys.executable, ABSIBLE_REQUIRE))
        os.system("%s -m pip install ansible-runner>=%s" % (sys.executable, ABSIBLER_REQUIRE))
        os.system("%s -m pip install sanic>=%s" % (sys.executable, SANIC_REQUIRE))
        try:
            import ansible
            import ansible_runner
        except ImportError:
            print("Error: I can NOT work without ansible-runner")
        # path = os.path.dirname(ansible.__file__)
        if LooseVersion(ansible.__version__) >= LooseVersion(ABSIBLE_REQUIRE) and \
                LooseVersion(pkg_resources.require("ansible_runner")[0].version) >= LooseVersion(ABSIBLER_REQUIRE):
            install.run(self)
            self.init_config_file()
            print("\033[1;37mAnsible-api v%s install complete.\033[0m" %
                  __version__)
        else:
            print("Error: ansible [%s] or ansible-runner [%s] version too low" %
                  (ansible_runner.__version__, pkg_resources.require("ansible_runner")[0].version))

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


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='ansible-api',
    version=__version__,
    scripts=['bin/ansible-api'],
    package_dir={'': 'src'},
    packages=find_packages('src'),
    python_requires='>=' + PYTHON_REQUIRE,
    install_requires=['sanic>=' + SANIC_REQUIRE,
                      'ansible>=' + ABSIBLE_REQUIRE,
                      'ansible-runner>=' + ABSIBLER_REQUIRE],
    cmdclass={'install': CustomInstall},

    author="lfbear",
    author_email="lfbear@gmail.com",
    description="A restful HTTP API for ansible",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GPLv3",
    url="https://github.com/lfbear/ansible-api",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/lfbear/ansible-api/issues',
        'Source': 'https://github.com/lfbear/ansible-api',
    },
)
