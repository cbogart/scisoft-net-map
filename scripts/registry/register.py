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
from snmweb.usage_cache import UsageCache
from Queue import Queue
from threading import Thread

queue = Queue()

def await():
    c = Connection()
    HOST = ''                 # Symbolic name meaning all available interfaces
    PORT = 7778               # Arbitrary non-privileged port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(3)
    usecache = UsageCache("snm-r", True, "R")  # True=assume logical link between "leaf" non-dependent packages
    while 1:
        conn, addr = s.accept()
        print 'Connection from', addr[0]
        data = ""
        while 1:
            rcvd = conn.recv(4096)
            if not rcvd: break
            data = data + rcvd
        conn.close()
        register(c, data, addr[0], usecache)
        
def scrub_dots(dottyDict):
    newdict = dict()
    for k in dottyDict:
        newdict[k.replace(".","[dot]")] = dottyDict[k]
    return newdict
    
def worker(): 
    while True:
        packet = queue.get()
        print "REGISTERING"
        usecache.registerPacket(record)
        queue.task_done()
        if queue.empty() and usecache.dirty:
            print "SAVING"
            usecache.saveToMongo()
       

def registerParsed(c, record, ip, usecache, dbraw="snm-raw-records"):
    try:
        rawrecords = c[dbraw]
        rawrecords["scimapInfo"].save(record)
        queue.put(record)
    except Exception as e:
        print "Error: ", e
        pdb.set_trace()

def register(c, data, ip, usecache, dbraw="snm-raw-records"):
    try:
        record = json.loads(data, object_hook = scrub_dots)
        record["receivedEpoch"] = int(time.time())
        record["ip"] = ip
        registerParsed(c, record, ip, usecache, dbraw)
    except Exception as e:
        print "Error: " + str(e)
        (r1,r2,r3) = sys.exc_info()
        print traceback.format_exception(r1,r2,r3)

def initializeThreads():
    t = Thread(target=worker)
    t.daemon = True
    t.start()
    await()

if __name__ == "__main__":
    initializeThreads()
