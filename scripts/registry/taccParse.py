#!/usr/bin/python

import json
import random
#import matplotlib.pyplot as plt
#from matplotlib.patches import Rectangle
import re
from os import walk
import os
from collections import defaultdict
from datetime import date, timedelta
from datetime import datetime as dt
import datetime
import pdb
import json
import copy
from register import scrub_dots, registerParsed, initializeThreads
from pymongo import Connection
from snmweb.usage_cache import freshDb, UsageCache
    
# Add exec to pkgT pointing to everything else
# add weakPkgDeps to stuff counted towards logical (in the other file)

def get_list_of_files(path):
    files = []
    for (root, dirnames, filenames) in walk(path):
        for filename in filenames:
            if ".json" in filename:
                files.append(os.path.join(root, filename))
    return files

def load_json(fname):
    appf = open(fname, "r")
    return json.loads(appf.read())

    if (pkgname in apps):
        inf = apps[pkgname]
    else:
        inf =  {
           "title" : pkgname,
           "description" : "unknown",
           "short_description" : "unknown",
           "image" : "unknown.jpg",
           "version" : "",
           "publications" : 0 }
    return inf

                
class Minimax:
    def __init__(self):
        self.min = 999999999
        self.max = -999999999
        self.count = 0
        self.sum = 0
    def reg(self, k):
        if (k<self.min): self.min=k
        if (k>self.max): self.max=k
        self.sum = self.sum + k
        self.count = self.count + 1
    def report(self):
        if (self.count == 0):
            return "No data received"
        else:
            return "Count = " + str(self.count) + " values were: " + str(self.min) + " < " + str(self.sum/self.count) + " < " + str(self.max)

allexecs = defaultdict(int)
execHasUserName = defaultdict(int)
execHasAccountName = defaultdict(int)
execTypes = defaultdict(int)
execExecType = defaultdict(set)
execTypeExamples = defaultdict(set)
users = defaultdict(int)
accounts = defaultdict(int)
runTime = Minimax()    
sha2exec = defaultdict(set)
exec2sha = defaultdict(set)
pkgParent = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

def regParent(parentname, json, depth):
    if (isinstance(json, list)):
        for j in json:
            pkgParent[j][parentname][depth] += 1
    elif (isinstance(json, dict)):
        for j in json:
            regParent(j, json[j], depth+1)
    else:
        pkgParent[json][parentname][depth] += 1
        
def analyze(rec):
    runTime.reg(int(float(rec["runTime"])))
    allexecs[rec["exec"]] += 1
    execHasUserName[rec["exec"]] += 1 if (rec["user"] in rec["exec"]) else 0
    execHasAccountName[rec["exec"]] += 1 if (rec["account"] in rec["exec"]) else 0
    users[rec["user"]] += 1
    accounts[rec["account"]] += 1
    execTypes[rec["execType"]] += 1    
    execExecType[rec["exec"]].add(rec["execType"])
    if rec["execType"].startswith("system:"):
        execTypeExamples[rec["execType"]].add(rec["exec"])
    sha2exec[rec["sha1"]].add(rec["exec"])
    exec2sha[rec["exec"]].add(rec["sha1"])
    regParent("pkgT", rec["pkgT"], 0)

headword = re.compile("([a-zA-Z]+)")
            

appExecs = defaultdict(set)
execApp = defaultdict(set)
exeUsers = defaultdict(set)

def getObviousName(exename):
    fnd = headword.match(exename)
    exenameFirst = exename if fnd is None else fnd.group(0)
    if len(exenameFirst) < 3:
        exenameFirst = "noObviousName"
    return exenameFirst


def buildAppnameTable(jobpart):
    global appExecs
    global exeUsers
    exename = jobpart["exec"].split("/")[-1]
    exenameFirst = getObviousName(exename)
    if (jobpart["execType"].startswith("system:")):
        name = jobpart["execType"][7:].split("/")[0]
        appExecs[name].add(exenameFirst)
        execApp[exenameFirst].add(name)

    exeUsers[exenameFirst].add(jobpart["user"])

def fiveOnly():
    for e in exeUsers:
        if len(exeUsers[e]) > 4 and e not in execApp and e not in appExecs and len(e) >= 3:
            appExecs[e].add(e)
            execApp[e].add(e)

        

def guessApp(jobpart):
    if (jobpart["execType"].startswith("system:")):
        return set([jobpart["execType"][7:].split("/")[0]])

    exename = jobpart["exec"].split("/")[-1]
    exenameFirst = getObviousName(exename)

    if (exenameFirst in execApp):
        return execApp[exenameFirst]

    allExeParts = [ss for ss in re.findall(headword, jobpart["exec"]) if len(ss) >=3]
    global nameCanon
    for ep in allExeParts:
        if ep in execApp:
            return execApp[ep]
    return set([])

def guess1App(jobpart):
    g = guessApp(jobpart)
    if (len(g) == 0):
       return ""
    else:
       return list(g)[0]
    

def forTaccDay(taccfiles):
    for fname in get_list_of_files(taccfiles):
        print fname
        yield load_json(fname)

def forTaccLongJob(taccfiles):
    for day in forTaccDay(taccfiles):
        users = defaultdict(list)
        for job in sorted(day.keys(), key=lambda k: int(k) if k.isdigit() else 999999999):
            users[day[job][0]["user"]] += day[job]
        for u in users:
            yield users[u]
            
       
def forTaccJob(taccfiles):
    for day in forTaccDay(taccfiles):
        for job in sorted(day.keys(), key=lambda k: int(k) if k.isdigit() else 999999999):
            yield day[job]

def forTaccPart(taccfiles):
    for job in forTaccJob(taccfiles):
        for jobpart in job:
            yield jobpart

def getLogicalDeps(sq):
    desc = defaultdict(set)
    prev = ""
    for elt in sq:
        if (elt != prev and elt != "" and prev != ""):
            desc[elt].add(prev)
        if (elt != ""):
            prev = elt
    return desc


def summarizeSequence(sq):
    desc = ""
    prev = ""
    for elt in sq:
        if (elt != prev):
            desc += elt 
        else:
            desc += "."
        prev = elt
    return desc

   
def importTaccData(taccfiles):
    c = Connection()
    c.drop_database("snm-tacc-raw")
    usecache = UsageCache(freshDb(c, "snm-tacc"), False, "TACC")
    initializeThreads(usecache)
    # Pass1: build appname table
    for jobpart in forTaccPart(taccfiles):
        buildAppnameTable(jobpart)

    fiveOnly()
    print "--------------------------------------------"

    nLabels = appExecs.keys()
    n = len(nLabels)
    #lookup = { nLabels[i]: i for i in range(0,n) }
    #dsm = numpy.zeros((n,n), dtype=numpy.int)

    jobsizeHist = defaultdict(int)
    counter = 0
    for job in forTaccLongJob(taccfiles):
       counter += 1
       jobsizeHist[len(job)] += 1

       # Make jobnum -> {start: N, end: N, appset: [a,b,c], follows: {J->delay, J->delay}}
       jobnum = defaultdict(dict)
       for j in job:
           id = j["jobID"]
           niceExec = guess1App(j)
           if id not in jobnum:
               jobnum[id]["start"] = int(j["startEpoch"])
               jobnum[id]["end"] = int(j["startEpoch"]) + int(float(j["runTime"]))
               if (niceExec != ''):
                   jobnum[id]["appset"] = set([niceExec])
               else:
                   jobnum[id]["appset"] = set([])
               jobnum[id]["follows"] = defaultdict(dict)
               jobnum[id]["logical"] = defaultdict(set)
           else:
               jobnum[id]["start"] = min(int(j["startEpoch"]), jobnum[id]["start"])
               jobnum[id]["end"] = max(int(j["startEpoch"]) + int(float(j["runTime"])), 
                                       jobnum[id]["end"])
               if (niceExec != ''):
                   jobnum[id]["appset"].add(niceExec)

       for j in jobnum:
           for k in jobnum:
               if j!=k:
                   if (jobnum[j]["end"] < jobnum[k]["start"]):
                       jobnum[k]["follows"][j] = jobnum[k]["start"] - jobnum[j]["end"]
                       for xc in (jobnum[k]["appset"] - jobnum[j]["appset"]):
                           jobnum[k]["logical"][xc] = jobnum[k]["logical"][xc].union(jobnum[j]["appset"] - jobnum[k]["appset"])


       for j in job:
           app = guess1App(j)
           if (app != ''):
               rec = copy.copy(j)
               rec["endEpoch"] = int(float(rec["startEpoch"])) + int(float(rec["runTime"]))
               rec["startTime"] = ""
               rec["dynDeps"] = []
               rec["exec"] = app
               rec["dynPackDeps"] = []
               rec["weakDeps"] = []
               jobinf = jobnum[rec["jobID"]]
               if (app in jobinf["logical"] and jobinf["logical"][app]):
                   rec["weakPackDeps"] = { app: list(jobinf["logical"][app]) }
               else:
                   rec["weakPackDeps"] = { }
               rec["weakPackDeps"] = scrub_dots(rec["weakPackDeps"])
               if (isinstance(rec["pkgT"], list)):
                   rec["pkgT"] = {}
               else:
                   rec["pkgT"] = { k: v["libA"] for (k,v) in rec["pkgT"].items() }
               rec["pkgT"][app] = rec["pkgT"].keys()
               rec["pkgT"] = scrub_dots(rec["pkgT"])
               data = json.dumps(rec)
               registerParsed(c, rec, "0.0.0.0", usecache, dbraw="snm-tacc-raw")
               prevapp = app
               prevapptime = rec["endEpoch"]


def hashColor(key, selected = False):
    """Return a color unique for this key, brigher if selected.

    Of course the color can't really be unique because there are more keys
    in the world than colors; but the algorithm tries to make similar strings
    come out different colors so they can be distinguished in a chart or graph"""

    def tw(t): return t ^ (t << (t%5)) ^ (t << (6+(t%7))) ^ (t << (13+(t%11)))
    theHash = tw(hash(key) % 5003)
    ifsel = 0x00 if selected else 0x80
    (r,g,b) = (ifsel |  (theHash & 0x7f),
               ifsel | ((theHash>>8) & 0x7F),
               ifsel | ((theHash>>16) & 0x7F))
    return "#{0:02x}{1:02x}{2:02x}".format(r,g,b)

def plotLongJob(lj):
    minx = 999999999999
    maxx = 0
    jobids = dict()
    print
    for part in lj:
        x = int(float(part["startEpoch"]))
        if x < minx: minx = x
        w = int(float(part["runTime"]))
        if x+w > maxx: maxx = x+w
        if (part["jobID"] not in jobids): jobids[part["jobID"]] = len(jobids.keys())
        y = jobids[part["jobID"]] + random.random()*.2
        h = 1
        c = hashColor(part["exec"])
        print part["exec"]
        plt.gca().add_patch(Rectangle((x,y),w,h,facecolor=c))
    plt.ylabel("some stuff")
    plt.axis([minx-1000, maxx+1000,0, 1+len(jobids.keys())])
    plt.show()


if __name__ == "__main__":
    #for job in forTaccLongJob(taccfiles):
    #    plotLongJob(job)
    
    importTaccData("/Users/cbogart/TACC-lariatData/")

