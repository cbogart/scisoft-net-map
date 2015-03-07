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
from snmweb.reposcrape import RepoScrape
from Queue import Queue
from threading import Thread

queue = Queue()

def worker(usecache): 
    while True:
        packet = queue.get()
        print packet["startEpoch"]
        usecache.registerPacket(packet)
        queue.task_done()
        if queue.empty() and usecache.dirty:
            usecache.saveToMongo()

def initializeThreads(usecache):
    t = Thread(target=worker, args=(usecache,))
    t.daemon = True
    t.start()

def finalizeThreads():
    while (not(queue.empty())):
        time.sleep(1)

if __name__ == "__main__":
    c = Connection()
    
    if len(sys.argv) < 4:
        print "Usage:", sys.argv[0], "<sqlite repo db>", "<mongo db>", "<appinfo file>"
        quit()

    sqlitedb = sys.argv[1]
    snmdb = sys.argv[2]
    appinfo = sys.argv[3]
    
    if (not os.path.isfile(sqlitedb)):
        print sqlitedb, "does not exist."
        quit()
     
    rs = RepoScrape(sqlitedb)
    rs.makeAppInfo()
    rs.writeAppInfo(appinfo)

    # True=assume logical link between "root" non-dependent packages
    c.drop_database(snmdb)
    usecache = UsageCache(openOrCreate(c, snmdb), True, "R")  

    initializeThreads(usecache)
    for raw in c["snm-raw-records"]["scimapInfo"].find():
        queue.put(raw)
    finalizeThreads()

    usecache.insertGitData(rs)
