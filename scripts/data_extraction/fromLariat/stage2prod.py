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
import pdb
from pymongo import MongoClient, Connection
from collections import defaultdict
from datetime import date, timedelta
from os import walk
from datetime import datetime as dt
from snmweb.db_objects import *

def readAppInfo():
    inf = json.load(open("app_info.json"))
    matches = dict()
    for i in inf:
        for m in i["match"]:
            matches[m] = i
    return matches

def readPubList(stagedb, proddb):
    publist = stagedb["pub_list"].find()
    for pubset in publist:
        proddb["pub_list"].insert(pubset)


class DataStreams():
    def __init__(self, datemin, datemax, default):
        self.daily = dict()
        self.weekly = dict()
        self.monthly = dict()
        self.total = default()
        day = datemin
        delta = datetime.timedelta(days=1)
        while day <= datemax:
            self.daily[dayOf(day)] = default()
            self.weekly[weekOf(day)] = default()
            self.monthly[monthOf(day)] = default()
            day += delta

    def add(self, day, count):
        self.total += count
        self.daily[dayOf(day)] += count
        self.weekly[weekOf(day)] += count
        self.monthly[monthOf(day)] += count

    def update(self, day, items):
        self.total.update(items)
        self.daily[dayOf(day)].update(items)
        self.weekly[weekOf(day)].update(items)
        self.monthly[monthOf(day)].update(items)

def xyList(f, datadict):
    return [{"x":str(k) ,"y":f(datadict[k])} for k in sorted(datadict.keys())]

def dayOf(when):
    return when.isoformat()

def weekOf(when):
    return (when + datetime.timedelta(days=-when.weekday())).isoformat()

def monthOf(when):
    return date(when.year, when.month, 1).isoformat()

def isTrending(whenYmd, enddate):
    return (enddate - ymd2date(whenYmd)).days < 60

def ymd2date(ymd): return dt.strptime(ymd, "%Y-%m-%d").date()

def date2ymd(dt): return dt.isoformat()

def populate(dbProductionName, userThreshhold=5):
    c = Connection()
    c.drop_database(dbProductionName)

    proddb = c[dbProductionName]
    stagedb = c["snm-staging"]


    print "Reading application data"
    matches = readAppInfo()

    print "Updating publication list"
    readPubList(stagedb, proddb)


    # Determine "legit" applications (more then 5 users)
    # Copy Application() table, filter to legit ones
    legitids = set()
    appcount = stagedb.application.count()
    checked= 0
    for app in stagedb.application.find():
        checked = checked + 1
        if (checked%100 == 0): print int(100.0*checked/appcount), "% done"

        appName = app["title"]
        # Skip some apps:
        if appName.startswith("-") or appName in ["a.out","date", "main", "test", "env", "hostname"]: #
            continue

        # fill in Application statistics
        id = app["_id"]
        use = stagedb["usage"].find_one({"application": id})
        users = stagedb["users_usage"].find_one({"application": id})
        user_list = stagedb["user_list"].find_one({"application": id})
        totalPubs = stagedb["pub_list"].find_one({"application": id})

        daymin = ymd2date(min([d["x"] for d in use["daily"]]))
        daymax = ymd2date(max([d["x"] for d in use["daily"]]))

        userListStreams = DataStreams(daymin, daymax, lambda: set([]))
        useStreams = DataStreams(daymin, daymax, lambda: 0)

        # Come up with distinct set of users per week, per month, and total; then count and add to users_usage
        for dayUsers in user_list["users"]:
           userListStreams.update(ymd2date(dayUsers["date"]), dayUsers["users"])

        if (len(userListStreams.total) < userThreshhold):
            #print appName,": only has ", len(userListStreams.total), "distinct users.  Skipping."
            continue
        print "Processing", appName, "because it has",len(userListStreams.total), "distinct users."

        legitids.add(app["_id"])
        proddb["users_usage"].save({ "application": id,
                   "daily": xyList(len, userListStreams.daily),
                   "weekly":xyList(len, userListStreams.weekly),
                   "monthly":xyList(len, userListStreams.monthly) })

        for dayUsage in use["daily"]:
            useStreams.add(ymd2date(dayUsage["x"]), dayUsage["y"])

        ident = lambda x:x
        proddb["usage"].save({ "application": id,
                   "daily": xyList(ident, useStreams.daily),
                   "weekly":xyList(ident, useStreams.weekly),
                   "monthly":xyList(ident, useStreams.monthly) })

        app["usage"] = useStreams.total
        app["usage_trend"] = sum([bds["y"] for bds in use["daily"] if isTrending(bds["x"], ymd2date("2013-02-01"))])
        app["publications"]= len(totalPubs["publications"]) if totalPubs is not None else 0
        app["image"] = "unknown.jpg"
        app["short_description"] = ""
        app["version"] = ""
        for m in matches:
            if (m in app["title"]):
                app["description"] = matches[m]["description"]
                app["image"] = matches[m]["image"]
                app["short_description"] = matches[m]["short_description"]
                app["title"] = app["title"] + " (" + matches[m]["title"] + ")"
                app["website"] = matches[m]["website"]
        app["users"] = len(userListStreams.total)
        proddb["application"].save(app)


    # Copy over legit portions of CoOccurence() table
    coocs = stagedb["co_occurence"].find()
    for cooc in coocs:
        app1 = cooc["application"]
        newlinks = []
        if (app1 in legitids):
            for link in cooc["links"]:
                app2 = link["app"]
                if (app2 in legitids):# and link["power"] > 2):
                    newlinks.append({
                        "app": app2,
                        "power": link["power"] })

            proddb["co_occurence"].insert(
                { "application": app1,
                  "links": newlinks })

if __name__ == "__main__":
    dbProductionName = "snm-web"
    dbStagingName = "snm-staging"
    mongo = connect(dbStagingName)
    #mongoStage = connect(dbStagingName, alias="default")
    print "All data from `{}` will be erased.".format(dbProductionName)
    raw_input("Press Enter to continue...")
    # TO DO: eventually we will not drop database, but instead be careful never to
    # put data in it twice, and make it just add one or more lariat records incrementally
    #mongo.drop_database(dbProductionName)
    #apptest()
    populate(dbProductionName)
    #retrieve_data()
