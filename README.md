# ansible-api
A restful http api for ansible 2.x

## What is it?
[Ansible] (https://github.com/ansible/ansible/) is a radically simple IT automation system.
If you are trying to use it and not like CLI mode, you can try me now. This is a http api for ansible

## How to install
python setup.py install

## How to use it

- configuration: /etc/ansible/api.cfg
- start in deamon mode: ansible-api -d > /dev/null &
- start in debug mode: ansible-api

## Why need to modify ansible code

I modified these code for getting more useful data in return, then you can do more actions according to return data.
Of course, you can diff the codes. I just added a private variate to record details in process and deal with them at last.
