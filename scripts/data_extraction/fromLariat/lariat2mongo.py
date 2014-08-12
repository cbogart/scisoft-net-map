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
import math
from collections import defaultdict
from datetime import date, timedelta
from os import walk
from snmweb.db_objects import *

class AppInfo:
    co_occurrence = defaultdict(lambda : defaultdict(int))   # app -> app -> add 1 each time they co-occur
    pubindex = defaultdict(list)
    projects_exec = defaultdict(set)

    def scanForJobData(self, file):
        usage = defaultdict(int)    # app -> add 1 for each time it's run ((for just today)
        users = defaultdict(set)   # app -> add each user who uses it
        byUser = defaultdict(set)

        content = open(file)
        data = json.loads(content.read());
        datakeys = sorted(data.keys())
        for job in datakeys:
            jobinf = data[job]
            for jobpart in jobinf:
                startdate = datetime.datetime.fromtimestamp(float(jobpart["startEpoch"])).date()
                collab = set()
                exeq = "/" + jobpart["exec"].split("/")[-1]
                collab.add(exeq)
                usage[exeq] += 1
                self.projects_exec[jobpart["account"]].add(exeq)
                users[exeq].add(jobpart["user"])
                byUser[jobpart["user"]].add(exeq)
                for pkgT in jobpart["pkgT"]:
                    pkgName = pkgT.split("/")[0]
                    collab.add(pkgName)
                    usage[pkgName] += 1
                    users[pkgName].add(jobpart["user"])
                    self.projects_exec[jobpart["account"]].add(pkgName)
                for c1 in collab:
                    for c2 in collab:
                        if (c1 != c2):
                            self.co_occurrence[c1][c2] += 1
        for u in byUser:
            if len(byUser[u]) > 1:
                for c1 in byUser[u]:
                    for c2 in byUser[u]:
                        if (c1 != c2):
                            self.co_occurrence[c1][c2] += 1

        return (startdate, usage, users)

    def readPubs(self):
        pubs = json.loads(open("pubs.json").read())
        for p in pubs:
            for project in p["projects"]:
                self.pubindex[project].append(p)
        pubs = None

    def getMaxCoocurrence(self, appusers):
        maxc = 1.0
        minusers = 5
        for app1 in self.co_occurrence:
            for app2 in self.co_occurrence[app1]:
                if math.log(self.co_occurrence[app1][app2]) > maxc and len(appusers[app1]) >= minusers and len(appusers[app2]) >= minusers:
                    maxc = math.log(self.co_occurrence[app1][app2])
        return (maxc, minusers)

def get_list_of_files(path):
    files = []
    for (root, dirnames, filenames) in walk(path):
        for filename in filenames:
            if ".json" in filename:
                files.append(os.path.join(root, filename))
    return files



def load_data(filedir):
    files = get_list_of_files(filedir)
    progress = 0
    l = len(files)
    #usagef = open("dailyusage.csv", "w")
    #usersf = open("dailyusers.csv", "w")
    #coocf = open("cooccurrence.csv", "w")

    appusers = defaultdict(set)
    weekuse = defaultdict(lambda: defaultdict(int))
    monthuse = defaultdict(lambda: defaultdict(int))
    weekusers = defaultdict(lambda: defaultdict(set))
    monthusers = defaultdict(lambda: defaultdict(set))

    appinfo = AppInfo()
    def addApp(appname):
        Application.objects(title=appname).update_one(upsert=True, set__title=appname, set__description="")
        app = Application.objects(title=appname).first()
        return app

    for f in files:
        progress += 1
        print "[{}%]\tprocessing {}".format(int(progress * 100 / l),
                                            os.path.basename(f))
        (dt, usage, users) = appinfo.scanForJobData(f)
        import pdb
        #pdb.set_trace()
        for appname in usage:
            app = addApp(appname)
            Usage.objects(application=app).update_one(upsert=True,
                          push__daily=ByDateStat(x=dt.isoformat(),y=usage[appname]))
            UsersUsage.objects(application=app).update_one(upsert=True,
                        push__daily=ByDateStat(x=dt.isoformat(),y=len(users[appname])))
            appusers[app].update(users[appname])
            UserList.objects(application=app).update_one(upsert=True,push__users=
                             ByDateUsers(users=users[appname],date=dt.isoformat()))

    (maxc, minusers) = appinfo.getMaxCoocurrence(appusers)

    for app1 in appinfo.co_occurrence:
        app1coocs = []
        for app2 in appinfo.co_occurrence[app1]:
            power = math.log(appinfo.co_occurrence[app1][app2])*(10.0/maxc)
            if (power > 1 and len(appusers[app1]) >=minusers and len(appusers[app2]) >= minusers):
                app1coos.append(Link(app=addApp(app2), power=power))
        if len(app1coocs) > 0:
            CoOccurence(application=addApp(app1), links=app1coocs).save()

    appinfo.readPubs()
    print len(appinfo.projects_exec), "projects ran code."
    print len(appinfo.pubindex), "projects listed publications"
    both = set(appinfo.projects_exec.keys()).intersection(set(appinfo.pubindex.keys()))
    print "Intersection size is", len(both)
    for b in both:
        appobj = Application.objects(application=appinfo.projects_exec[b]).first()
        PubList.objects(application=appobj).update_one(upsert=True,push__publications=
                 PubInfo(**appinfo.pubindex[b]))

"""
def load_data(filename="db_sample.json",
              hash_file_path="sample_usage/21-applications",
              usage_path="sample_usage",
              usage_users_path="sample_usage_users"):
    all_apps = load_apps(filename)
    f = open(hash_file_path)
    hash_list = f.readlines()
    hash_iterator = iter(hash_list)
    for app in all_apps:
        hash = hash_iterator.next()[:10]
        load_stat(app, hash, usage_path, "Usage")
        load_stat(app, hash, usage_users_path, "UsersUsage")
        load_distinct_users_number(app, hash, usage_users_path)
        load_usage_summary(app)
    generate_links(all_apps)


def retrieve_data():
    print("Done:")
    for app in Application.objects:
        print " * ", app.title
        x = Usage.objects().count()
    print("Done: {} sample applications loaded".format(x))
"""

if __name__ == "__main__":
    dbProduction = "snm-web"
    dbStaging = "snm-staging"
    if len(sys.argv) < 1:
        print "usage: {} ~/TACC-LariatData".format(
            sys.argv[0])
        exit(1)
    filedir = sys.argv[1]
    mongo = connect(dbStaging)
    print "All data from `{}` will be erased.".format(dbStaging)
    raw_input("Press Enter to continue...")
    # TO DO: eventually we will not drop database, but instead be careful never to
    # put data in it twice, and make it just add one or more lariat records incrementally
    mongo.drop_database(dbStaging)
    load_data(filedir)
    #retrieve_data()
