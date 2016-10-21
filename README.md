# ansible-api
A restful http api for ansible 2.x

## What is it?
[Ansible] (https://github.com/ansible/ansible/) is a radically simple IT automation system.
If you are trying to use it and not like CLI mode, you can try me now. This is a http api for ansible

## Changelog

- 0.2.0 support websocket, remove code invaded in ansible

## How to install
python setup.py install

## How to use it

- configuration: /etc/ansible/api.cfg
- start in deamon mode: ansible-api -d >> /var/log/ansible-api-process.log 2>&1 &
- start in debug mode: ansible-api

## How to prepare your data

[HTTP API Usage](https://github.com/lfbear/ansible-api/wiki/http-api-usage)
