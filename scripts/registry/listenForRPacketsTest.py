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
from Queue import Queue
from threading import Thread

queue = Queue()

def await(c):
    HOST = ''                 # Symbolic name meaning all available interfaces
    PORT = 7978               # Arbitrary non-privileged port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(3)
    while 1:
        conn, addr = s.accept()
        print 'Connection from', addr[0]
        data = ""
        while 1:
            rcvd = conn.recv(4096)
            if not rcvd: break
            data = data + rcvd
        conn.close()
        register(c, data, addr[0])
        
def scrub_dots(dottyDict):
    newdict = dict()
    for k in dottyDict:
        newdict[k.replace(".","[dot]")] = dottyDict[k]
    return newdict
    
def registerParsed(c, record, ip, dbraw="snm-raw-records-test"):
    try:
        rawrecords = c[dbraw]
        rawrecords["scimapInfo"].save(record)
    except Exception as e:
        print "Error: ", e
        pdb.set_trace()

def register(c, data, ip, dbraw="snm-raw-records-test"):
    try:
        record = json.loads(data, object_hook = scrub_dots)
        record["receivedEpoch"] = int(time.time())
        registerParsed(c, record, ip, dbraw)
    except Exception as e:
        print "Error: " + str(e)
        (r1,r2,r3) = sys.exc_info()
        print traceback.format_exception(r1,r2,r3)

if __name__ == "__main__":
    c = Connection()
    
    await(c)
