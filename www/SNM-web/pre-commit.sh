#!/bin/sh

git stash -q --keep-index
python www/SNM-web/snmweb/setup.py test -q
RESULT=$?
git stash pop -q
[ $RESULT -ne 0 ] && exit 1
exit 0
