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

def worker(usecache): 
    while True:
        packet = queue.get()
        print packet
        usecache.registerPacket(packet)
        queue.task_done()
        if queue.empty() and usecache.dirty:
            usecache.saveToMongo()

def initializeThreads(usecache):
    t = Thread(target=worker, args=(usecache,))
    t.daemon = True
    t.start()

if __name__ == "__main__":
    c = Connection()
    
    # True=assume logical link between "root" non-dependent packages
    c.drop_database("snm-r")
    usecache = UsageCache(openOrCreate(c, "snm-r"), True, "R")  

    initializeThreads(usecache)
    for raw in c["snm-raw-records"]["scimapInfo"].find():
        print (raw["startTime"])
        queue.put(raw)
    while (not(queue.empty())):
        time.sleep(1)
