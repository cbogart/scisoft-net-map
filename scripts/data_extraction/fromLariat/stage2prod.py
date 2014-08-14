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

def enoughUsers2(userThreshhold):
    users = set()
    apps = set()

    for bydateusers in UserList.objects(application=app).first().users:
        users.update(set(bydateusers.users))
        if len(users) >= userThreshhold:
            return True
    return len(users) >= userThreshhold

def enoughUsers(app, stagedb, userThreshhold):
    if (app["title"].startswith("-")):
        return False
    users = set()
    #print dir(app), str(app)
    for bydateusers in stagedb["user_list"].find_one(
                    {"application": app["_id"]})["users"]:
        users.update(set(bydateusers["users"]))
        if len(users) >= userThreshhold:
            return True
    return len(users) >= userThreshhold

def populate(dbProductionName, userThreshhold=5):
    c = Connection()
    c.drop_database(dbProductionName)

    proddb = c[dbProductionName]
    stagedb = c["snm-staging"]

    print "Type of proddb is", type(proddb), "and its app object is", proddb["application"]

    legit = dict()
    legitids = set()
    # Determine "legit" applications (more then 5 users)
    # Copy Application() table, filter to legit ones
    appcount = stagedb.application.count() #Application.objects.count()
    checked= 0
    for app in stagedb.application.find(): #Application.objects:
        checked = checked + 1
        if (checked%100 == 0): print int(100.0*checked/appcount), "% done"
        if enoughUsers(app, stagedb, userThreshhold):
            legit[app["title"]] = app
            legitids.add(app["_id"])
            print app["title"], "has enough users"
        #if checked == 500:
        #    break

    for appname in legit:
        proddb["application"].insert(legit[appname])
        #legitNew[appname] = proddb["Application"].insert(legit[appname])

    matches = readAppInfo()
    for appName in legit:
        # fill in Application statistics
        id = legit[appName]["_id"]
        use = stagedb["usage"].find_one({"application": id})
        totalUse = sum([bds["y"] for bds in use["daily"]])
        trend = sum([bds["y"] for bds in use["daily"] if bds["x"][0:4]=="2014"])  # FIX ME: within 2 months
        users = stagedb["users_usage"].find_one({"application": id})
        totalUsers = sum([bds["y"] for bds in users["daily"]])
        totalPubs = stagedb["pub_list"].find_one({"application": id})

        prodApp = proddb["application"].find_one({"_id": id})
        prodApp["usage"] = totalUse
        prodApp["usage_trend"] = trend
        prodApp["users"] = totalUsers
        prodApp["publications"]= len(totalPubs["publications"]) if totalPubs is not None else 0
        prodApp["image"] = "unknown.jpg"
        prodApp["short_description"] = ""
        prodApp["version"] = ""
        for m in matches:
            if (m in prodApp["title"]):
                prodApp["description"] = matches[m]["description"]
                prodApp["image"] = matches[m]["image"]
                prodApp["short_description"] = matches[m]["short_description"]
                prodApp["title"] = matches[m]["title"] + "--" + prodApp["title"]
                prodApp["website"] = matches[m]["website"]

        proddb["application"].save(prodApp)


        # TODO: look up application data in app_info.json


        # Copy usage and users_usage over for legit applications
        weekly = defaultdict(int)
        monthly = defaultdict(int)
        for day in use["daily"]:
            when = dt.strptime(day["x"], "%Y-%m-%d")
            week = when + datetime.timedelta(days=-when.weekday(), weeks=1)
            #week = week.__str__()
            month = date(when.year, when.month, 1) #.__str__()
            weekly[week] += day["y"]
            monthly[month] += day["y"]
        newuse = { "application": id,
                   "daily": use["daily"],
                   "weekly":[{"x":str(wk) ,"y":weekly[wk]} for wk in sorted(weekly.keys())],
                   "monthly":[{"x":str(mo) ,"y":monthly[mo]} for mo in sorted(monthly.keys())] }
        proddb["usage"].save(newuse)

    # Copy over legit portions of CoOccurence() table
    coocs = stagedb["co_occurence"].find()
    for cooc in coocs:
        app1 = cooc["application"]
        newlinks = []
        if (app1 in legitids):
            for link in cooc["links"]:
                app2 = link["app"]
                if (app2 in legitids):
                    newlinks.append({
                        "app": app2,
                        "power": link["power"] })

            proddb["co_occurence"].insert(
                { "application": app1,
                  "links": newlinks })


"""
        # NO THIS IS WRONG BECAUSE USERS OVERLAP
        for day in users.daily:
            when = dt.strptime(day.x, "%Y-%m-%d")
            week = when + datetime.timedelta(days=-when.weekday(), weeks=1)
            #week = week.__str__()
            month = date(when.year, when.month, 1) #.__str__()
            weekly[week] += day.y
            monthly[month] += day.y
        newuse = { "application": legitNew[appname],
                   "daily": use.daily,
                   "weekly":
                        proddb["Usage"].insert(
                            [{"x":str(wk) ,"y":weekly[wk]} for wk in sorted(weekly.keys())]),
                   "monthly":
                        proddb["Usage"].insert(
                            [{"x":str(mo) ,"y":monthly[mo]} for mo in sorted(monthly.keys())]) }
        proddb["Usage"].save(newuse)


        # TODO: compute weekly and monthly data streams for usage
        # TODO: compute users_usage from UserList
"""

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
