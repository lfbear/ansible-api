# ansible-api
A restful http api for ansible 2.x

## What is it?
ansible is a radically simple IT automation system [Ansible at Github] (https://github.com/ansible/ansible/) . 
If you are triing to use it and not like CLI mode, you can try me now. This is a http api for ansible

## how to install
choose your ansble version folder, and copy files to your disk.

- bin/ansible-api --> /usr/bin/ansible-api
- lib/* --> /usr/lib/python2.x/site-packages/ansible-2.2.0-py2.x.egg/

## how to use it

- start in deamon mode: ansible-api -d > /dev/null &
- start in debug mode: ansible-api
