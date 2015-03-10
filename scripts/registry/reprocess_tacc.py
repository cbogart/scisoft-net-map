#!/usr/bin/python
#
# Author:
#  Chris Bogart
#
import json
import sys
import os
import datetime
import time
import math
import pdb
import traceback
import socket
from pymongo import MongoClient, Connection
from collections import defaultdict
from datetime import date, timedelta
from os import walk
from datetime import datetime as dt
from snmweb.db_objects import *
from snmweb.usage_cache import UsageCache, openOrCreate
from Queue import Queue
from threading import Thread

queue = Queue()
lastday = "2000-01-01";

def worker(usecache): 
    global lastday
    while True:
        packet = queue.get()
        dt = time.strftime('%Y-%m-%d', time.localtime(int(packet["startEpoch"])+0))
        #print packet["startEpoch"]
        if (dt > lastday):
            print dt
            lastday = dt
        usecache.registerPacket(packet)
        if queue.empty() and usecache.dirty:
            usecache.saveToMongo()
        queue.task_done()

def initializeThreads(usecache):
    t = Thread(target=worker, args=(usecache,))
    t.daemon = True
    t.start()

if __name__ == "__main__":
    c = Connection()
    
    # True=assume logical link between "root" non-dependent packages
    c.drop_database("snm-tacc")
    usecache = UsageCache(openOrCreate(c, "snm-tacc"), True, "TACC", useWeakDeps=True)  

    initializeThreads(usecache)
    rownum = 0
    try:
        for raw in c["snm-tacc-raw"]["scimapInfo"].find(timeout=False):
            rownum += 1
            queue.put(raw)
        while (not(queue.empty())):
            time.sleep(1)
        print "Spooling through queued packets at row#", rownum
        queue.join()
        print "Saving"
        if usecache.dirty:
            usecache.saveToMongo()
        print "Saved."
    finally:
        c.close()
