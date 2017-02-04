# ansible-api
A restful http api for ansible 2.x

## What is it?
[Ansible] (https://github.com/ansible/ansible/) is a radically simple IT automation system.
If you are trying to use it and not like CLI mode, you can try me now. This is a http api for ansible

## Changelog

- 0.2.1 optimize log and allow mutil-instance in the same host
- 0.2.0 support websocket, remove code invaded in ansible

## How to install
- git clone https://github.com/lfbear/ansible-api.git
- python setup.py install

## How to use it

- default configuration: /etc/ansible/api.cfg
- start: 
```
ansible-api -c [Configfile, Optional] -d [Daemon Mode, Optional]
```
eg: ansible-api -c /etc/ansible/api.cfg -d > /dev/null &

## How to prepare your data

[HTTP API Usage](https://github.com/lfbear/ansible-api/wiki/http-api-usage)

## If you have hundreds of machines, suggest
[filedescriptor out of range in select()](https://github.com/lfbear/ansible-api/wiki/ValueError:-filedescriptor-out-of-range-in-select())
