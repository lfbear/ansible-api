# ansible-api v0.5.0

A restful http api for ansible
python version >= 3.7

## What is it?

[Ansible](https://github.com/ansible/ansible/) is a radically simple IT automation system.
If you are trying to use it and not like CLI, you can try me now. I can provide you use ansible by A RESTful HTTP Api and a realtime processing message (websocket api), you can see all details.

## Changelog

- 0.5.0 replace tornado with sanic, more lightly (python>=3.7) 
- 0.3.0 using ansible-runner as middleware
- 0.2.6 adaptive ansible 2.6.4 and add asynchronization mode
- 0.2.2 optimize log
- 0.2.1 optimize log and allow mutil-instance in the same host
- 0.2.0 support websocket, remove code invaded in ansible

## Structure chart

![image](https://github.com/lfbear/ansible-api/raw/master/data/structure.png)

## How to install

- [preparatory work] python version >= 3.7 (use asyncio featrue)
- ```pip3 install ansible-api```

## How to start it

- default configuration: /etc/ansible/api.cfg
- start: 
```
ansible-api -c [Configfile, Optional] -d [Daemon Mode, Optional]
```
eg: ansible-api -c /etc/ansible/api.cfg -d > /dev/null &

## How to prepare your data

[HTTP API Usage](https://github.com/lfbear/ansible-api/wiki/http-api-usage)
