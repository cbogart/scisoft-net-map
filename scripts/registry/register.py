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
import socket
from pymongo import MongoClient, Connection
from collections import defaultdict
from datetime import date, timedelta
from os import walk
from datetime import datetime as dt
from snmweb.db_objects import *
from processUsageRecsOnline import addOne

def await():
    c = Connection()
    HOST = ''                 # Symbolic name meaning all available interfaces
    PORT = 7778               # Arbitrary non-privileged port
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
    
def register(c, data, ip):
    try:
        rawrecords = c["snm-raw-records"]
        record = json.loads(data, object_hook = scrub_dots)
        record["ip"] = ip
        rawrecords["scimapInfo"].save(record)
        addOne(c, c["snm-r"], record)
        print "Registered a usage! from ", ip
        print record
    except Exception as e:
        print "Error: " + str(e)



if __name__ == "__main__":
	await()
