#!/bin/bash
. ../../env/bin/activate
cd ../snmweb
nosetests -c nose.cfg
