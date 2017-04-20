#!/bin/sh

cd ~/high-quality-chat
git checkout master
git pull
python hqc/chat/ChatServer.py &