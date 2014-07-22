#!/bin/bash

cd /var/www/SNM
git checkout master
git pull origin master
killall pserve
cd www/SNM-web
pserve production.ini start --daemon --pid-file=/var/www/5000.pid --log-file=/var/www/5000.log --monitor-restart

