#!/usr/bin/python
#
# Authors:
#  Chris Bogart, Nikita Chepanov, Biao "Leo" Ma, Svyatoslav "Slava" Kovtunenko
#
import json
import sys
import os
import datetime
import time
from collections import defaultdict
from datetime import date, timedelta
from os import walk

co_occurrence = defaultdict(lambda : defaultdict(int))   # app -> app -> add 1 each time they co-occur
pubindex = defaultdict(list)
projects_exec = defaultdict(set)



def scanForJobData(file):
    usage = defaultdict(int)    # app -> add 1 for each time it's run ((for just today)
    users = defaultdict(set)   # app -> add each user who uses it
    byUser = defaultdict(set)

    content = open(file)
    data = json.loads(content.read());
    datakeys = sorted(data.keys())
    for job in datakeys:
        #print "Job: " + str(job)
        jobinf = data[job]
        for jobpart in jobinf:
            startdate = datetime.datetime.fromtimestamp(float(jobpart["startEpoch"])).date()
            collab = set()
            #print "\t" + jobpart["startTime"] + "\t" + jobpart["exec"].split("/")[-1]
            exeq = "/" + jobpart["exec"].split("/")[-1]
            collab.add(exeq)
            usage[exeq] += 1
            projects_exec[jobpart["account"]].add(exeq)
            users[exeq].add(jobpart["user"])
            byUser[jobpart["user"]].add(exeq)
            for pkgT in jobpart["pkgT"]:
                pkgName = pkgT.split("/")[0]
                collab.add(pkgName)
                usage[pkgName] += 1
                users[pkgName].add(jobpart["user"])
                projects_exec[jobpart["account"]].add(pkgName)
            for c1 in collab:
                for c2 in collab:
                    if (c1 != c2):
                        co_occurrence[c1][c2] += 1
    for u in byUser:
        if len(byUser[u]) > 1:
            for c1 in byUser[u]:
                for c2 in byUser[u]:
                    if (c1 != c2):
                        co_occurrence[c1][c2] += 1

    return (startdate, usage, users, co_occurrence)

def get_list_of_files(path):
    files = []
    for (root, dirnames, filenames) in walk(path):
        for filename in filenames:
            if ".json" in filename:
                files.append(os.path.join(root, filename))
    return files

def readPubs():
    pubs = json.loads(open("pubs.json").read())
    for p in pubs:
        for project in p["projects"]:
            pubindex[project].append(p)
    pubs = None

def main():
    if len(sys.argv) < 2:
        print "usage: {} ~/TACC-LariatData".format(
            sys.argv[0])
        return
    files = get_list_of_files(sys.argv[1])
    progress = 0
    l = len(files)
    usagef = open("dailyusage.csv", "w")
    usersf = open("dailyusers.csv", "w")
    coocf = open("cooccurrence.csv", "w")

    appusers = defaultdict(set)
    weekuse = defaultdict(lambda: defaultdict(int))
    monthuse = defaultdict(lambda: defaultdict(int))
    weekusers = defaultdict(lambda: defaultdict(set))
    monthusers = defaultdict(lambda: defaultdict(set))

    for f in files:
        progress += 1
        print "[{}%]\tprocessing {}".format(int(progress * 100 / l),
                                            os.path.basename(f))
        (dt, usage, users, co) = scanForJobData(f)
        for app in usage:
            usagef.write('''"{app}",{dt},{usage}\n'''.format(app=app,dt=dt,usage=usage[app]))
            usersf.write('''"{app}",{dt},{users}\n'''.format(app=app,dt=dt,users=len(users[app])))
            appusers[app].update(users[app])

    maxc = 1.0
    minusers = 5
    import math
    for app1 in co_occurrence:
        for app2 in co_occurrence[app1]:
            if math.log(co_occurrence[app1][app2]) > maxc and len(appusers[app1]) >= minusers and len(appusers[app2]) >= minusers:
                maxc = math.log(co_occurrence[app1][app2])
                print "Max cooc = ", maxc

    for app1 in co_occurrence:
        for app2 in co_occurrence[app1]:
            power = math.log(co_occurrence[app1][app2])*(10.0/maxc)
            if (power > 1 and len(appusers[app1]) >=minusers and len(appusers[app2]) >= minusers):
                coocf.write('''"{app1}",{app2},{power}\n'''.format(app1=app1, app2=app2, power=int(power)))


    print len(projects_exec), "projects ran code."
    print len(pubindex), "projects listed publications"
    both = set(projects_exec.keys()).intersection(set(pubindex.keys()))
    print "Intersection size is", len(both)
    for b in both:
        print "---------",b
        print projects_exec[b]
        print [(inf["year"], inf["title"]) for inf in pubindex[b]]
        print


if __name__ == '__main__':
    main()
