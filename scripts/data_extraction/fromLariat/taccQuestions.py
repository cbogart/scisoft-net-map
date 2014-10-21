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
import numpy
import json
import cPickle
    
#

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

                
#
#  does each jobid occur exactly once, on one day?           YES
#  is startEpoch always on the same day as the file?         ...
#  What is the range of runTime                              ___
#  What is the list of ALL exec fields                       ___
#  What is the list of all execType                          ___
#  Flag exec fields that have the user's name in their path  ___
#  What is the list of ALL accounts                          ___
#  What is the list of all users                             ___
#  Find sha1's the same that have different execs            ___
#  Find exec the same that have different sha1               ___
#  For each item in the pkgT trees, list level and parent item, and count unique instances of
#     that combo of level and parent.                        ___
#  In path:
#     find username
#     subst digit strings for DDDDD
#     report pre-username part of path

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
def summarize():
    print "Runtime: ", runTime.report()
    print "ExecTypes: "
    for k in execTypes:
        print "\t", k, execTypes[k]
        for k1 in execTypeExamples[k]:
            print "\t\t", k1
    with open("sha.csv", "w") as f:
        for sha in sha2exec:
             f.write(sha + ", " + ", ".join(sha2exec[sha]) + "\n")
    with open("packages.csv", "w") as f:
        for ch in sorted(pkgParent):
            for par in sorted(pkgParent[ch]):
                for depth in pkgParent[ch][par]:
                    f.write( ch + "," + par + ", " + str(depth) + ", " + str(pkgParent[ch][par][depth]) + "\n")
    with open("execs.csv", "w") as f:
        for x in sorted( allexecs):
            exename = x.split("/")[-1]
            fnd = headword.match(exename)
            exenameFirst = exename if fnd is None else fnd.group(0)
            itsTypes = ":".join(execExecType[x])
            f.write(x + ", " + str(allexecs[x]) + ", " + exename + ", " + exenameFirst + ", " + itsTypes + ", " + str(execHasUserName[x]) + ", " + str(execHasAccountName[x]) + ", " + ", ".join(exec2sha[x]) + "\n")
    with open("users.csv", "w") as f:
        for x in sorted(users):
            f.write(x + "\n")
    with open("accounts.csv", "w") as f:
        for x in sorted(accounts):
            f.write(x + "\n")
            

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
    for fname in get_list_of_files("/Users/bogart-MBP-isri/TACC-lariatData"):
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

   
def makeDsm():
    # Pass1: build appname table
    for jobpart in forTaccPart():
        buildAppnameTable(jobpart)

    fiveOnly()
    print "--------------------------------------------"

    nLabels = appExecs.keys()
    n = len(nLabels)
    lookup = { nLabels[i]: i for i in range(0,n) }
    dsm = numpy.zeros((n,n), dtype=numpy.int)

    jobsizeHist = defaultdict(int)
    for job in forTaccLongJob():
       jobsizeHist[len(job)] += 1
       logdeps = getLogicalDeps([guess1App(j) for j in job])
       for dep in logdeps:
           for ref in logdeps[dep]:
               try:
                   dsm[lookup[dep],lookup[ref]] += 1
               except:
                   pdb.set_trace()
      
    with open("pickle", "w") as f:
        cPickle.dump( (dsm, nLabels), f)

def swapper(dsm, nLabels, lookup, aname, bname):
    a = lookup[aname]
    b = lookup[bname]
    dsm[:, [a,b]] = dsm[:, [b,a]]
    dsm[[a,b], :] = dsm[[b,a], :]
    nLabels[a] = bname
    nLabels[b] = aname
    lookup[aname] = b
    lookup[bname] = a

def reorderBy(lam, nLabels, lookup, dsm, n):
    neworder = nLabels[:]
    neworder.sort(f)
    newindexing = [lookup[lab] for lab in neworder]
    dsm[:, range(0,n)] = dsm[:, newindexing]
    dsm[range(0,n), :] = dsm[newindexing, :]
    nLabels = {old: nLabels[newindexing[old]] for old in range(0,n)}
    lookup = { nLabels[i]: i for i in range(0,n) }


def htmlizeFromDump():
    with open("pickle", "r") as f:
        (dsm, nLabels) = cPickle.load(f)
    n = len(nLabels)
    lookup = { nLabels[i]: i for i in range(0,n) }
    for i in range(0,n): dsm[i,i] = 500

    reorderBy(lambda lab: -numpy.count_nonzero(dsm[:,lookup[lab]]))

    htmlize(n, dsm, nLabels)


def htmlize(n, dsm, nLabels):
    import math
    with open("dsm.html", "w") as f:
        f.write("""
<style> 
   table {
      table-layout: fixed; 
   } 
   th.rotated { 
      height: 140px; 
   } 
   th.rotated > div {
      transform: 
         translate(20px, 41px) 
         rotate(315deg); 
      width: 22px; 
   } 
   th.rotated > div > span { 
      border-bottom: 1px solid #ccc; 
      padding: 5px 5px; 
   } 
</style>\n""")
        f.write("<table>\n")
        f.write("<tr><th></th>")
        for col in range(0,n): 
           f.write("<th class=\"rotated\"><div><span>%s</span></div></th>" % (nLabels[col]))
        f.write("</tr>\n")
        for row in range(0,n):
           f.write("<tr>")
           f.write("<th><div><span>%s</span></div></th>" % (nLabels[row]))
           for col in range(0,n):
              degree= (255 - min(255, 40*math.log(dsm[row,col]+1)))
              f.write("<td bgcolor=\"#ff%02x%02x\"></td>" % (degree, degree))
           f.write("</tr>")
        f.write("</table>")
       

if __name__ == "__main__":
    htmlizeFromDump() 

def oldPass2():
    # Pass2: classify!
    classified = 0
    checked = 0
    with open("classify.csv", "w") as f:
        for jobpart in forTaccPart():
            checked = checked + 1
            if guessApp(jobpart) != set([]):
                classified = classified + 1
                f.write("%s,%s,%s\n" % ( list(guessApp(jobpart))[0], jobpart["execType"], jobpart["exec"]))
            else:
                f.write("unknown, %s,%s\n" % ( jobpart["execType"], jobpart["exec"]))

            if checked % 10000 == 0:
                print classified, "/", checked, jobpart["exec"].split("/")[-1], jobpart["execType"], guessApp(jobpart)
        
    print classified*100/checked,"% classified"

def oldWay():
    try:
        for jobpart in forTaccPart():
            analyze(jobpart)
    except Exception, e:
        print str(e)
    summarize()
        
