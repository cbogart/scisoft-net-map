#!/usr/bin/python

import json
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
from register import register, scrub_dots, registerParsed
from pymongo import Connection
    
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
    

def forTaccDay():
    for fname in get_list_of_files("/Users/bogart-MBP-isri/TACC-lariatData/"):
        print fname
        yield load_json(fname)

def forTaccLongJob():
    for day in forTaccDay():
        users = defaultdict(list)
        for job in day:
            users[day[job][0]["user"]] += day[job]
        for u in users:
            yield users[u]
            
       
def forTaccJob():
    for day in forTaccDay():
        for k in day:
            yield day[k]

def forTaccPart():
    for job in forTaccJob():
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

   
def importTaccData():
    # Pass1: build appname table
    for jobpart in forTaccPart():
        buildAppnameTable(jobpart)

    fiveOnly()
    print "--------------------------------------------"

    nLabels = appExecs.keys()
    n = len(nLabels)
    #lookup = { nLabels[i]: i for i in range(0,n) }
    #dsm = numpy.zeros((n,n), dtype=numpy.int)

    c = Connection()
    c.drop_database("snm-tacc")

    jobsizeHist = defaultdict(int)
    for job in forTaccLongJob():
       jobsizeHist[len(job)] += 1
       #logdeps = getLogicalDeps([guess1App(j) for j in job])
       prevapp = ""
       for j in job:
           app = guess1App(j)
           if (app != ''):
               rec = copy.copy(j)
               rec["endEpoch"] = rec["startEpoch"] + rec["runTime"]
               rec["startTime"] = ""
               rec["dynDeps"] = []
               rec["exec"] = app
               rec["dynPackDeps"] = []
               rec["weakDeps"] = []
               if (prevapp != "" and app != "" and app != prevapp):
                   rec["weakPackDeps"] = { app: [prevapp] }
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
               registerParsed(c, rec, "0.0.0.0", dbraw="snm-tacc-raw", dbcooked="snm-tacc", postponeCalc = True)
               prevapp = app
    recalcApps(c, c["snm-tacc"])
      

    #with open("pickle", "w") as f:
    #    cPickle.dump( (dsm, nLabels), f)


if __name__ == "__main__":
    importTaccData()
