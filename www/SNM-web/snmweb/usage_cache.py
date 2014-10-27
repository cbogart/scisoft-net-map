#!/usr/bin/python

from pymongo import MongoClient, Connection
import json
from collections import defaultdict
from datetime import date, timedelta
from datetime import datetime as dt
import datetime
import pdb
import json
from threading import Lock

usageCacheLock = Lock()

def openOrCreate(c, dbname):
    if "global_stats" in c[dbname].collection_names():
       return c[dbname]
    else:
       return freshDb(c, dbname)

def freshDb(c, dbname):
    c.drop_database(dbname)
    db = c[dbname]
    db.global_stats.save({"max_co_uses": { "static": 0, "logical": 0}, "max_publications": 0 })
    return db

def readAppInfo(sci_platform):
    inf = json.load(open("../../data/appinfo." + sci_platform + ".json"))
    matches = dict()
    if (isinstance(inf, dict)):
        for i in inf:
            for m in inf[i]["match"]:
                matches[m] = inf[i]
    else: # if it's a list
        for i in inf:
            for m in i["match"]:
                matches[m] = i
    return matches

def readPubInfo(sci_platform):
    byproject = defaultdict(set)
    inf = []
    try:
        inf = json.load(open("../../data/pubs." + sci_platform + ".json"))
        for i in range(len(inf)):
            for p in inf[i]["projects"]:
                byproject[p].add(i)
    except Exception, e:
        print "ERROR: ", str(e)
    return (byproject, inf)


class UsageCache:

    def __init__(self, dest, logicallyLinkRoots, sci_platform):
        "Load a fresh database from mongo"

        self.logicallyLinkRoots = logicallyLinkRoots
        self.sci_platform = sci_platform
        self.app_info = readAppInfo(sci_platform)
        (self.pub_indexes, self.pub_list) = readPubInfo(sci_platform)
        with usageCacheLock:
            self.today = datetime.date.today()
            self.db = dest
            self.apps = dict()
            self.dirty = False
            self.appIds = {}
            for app in dest.application.find():
                self.apps[app["title"]] = { 
                   "id": app["_id"],
                   "usage": defaultdict(int),
                   "user_list": defaultdict(list),
                   "pub_indexes": set(),
                   "co_occurence": defaultdict(lambda: {"static": 0, "logical": 0} )
                }
                self.appIds[app["_id"]] = app["title"]
           
            for a_publist in dest.pub_list.find():
                appname = self.appIds[a_publist["application"]]
                try:
                    self.apps[appname]["pub_indexes"] = set(
                         [self.pub_list.index(pub) for pub in a_publist["publications"]])
                except Exception, e:
                    print "Should not happen: publication should be in the list"
                    print str(e)
                    pdb.set_trace()

            for a_usage in dest.usage.find():
                appname = self.appIds[a_usage["application"]]
                self.apps[appname]["usage"] = pairlist2dict(a_usage["daily"], "x", "y")
    
            for a_user_list in dest.user_list.find():
                appname = self.appIds[a_user_list["application"]]
                self.apps[appname]["user_list"] = pairlist2dict(a_user_list["users"], "date", "users")
    
            gs = dest.global_stats.find_one()
            self.max_co_uses = gs["max_co_uses"]

            for cooc in dest.co_occurence.find():
                appname = self.appIds[cooc["application"]]
                for otherapp in cooc["links"]:
                     otherappname = self.appIds[otherapp["app"]]
                     self.apps[appname]["co_occurence"][otherappname] = otherapp["co_uses"]
                     self.update_max_co_use(otherapp["co_uses"])
            
    # Import of old data for demonstration purposes (e.g. TACC data)
    # may require a different definition of "today" to get a reasonable
    # representation of what's "trending"
    #
    def defineToday(self, thedate):
        self.today = thedate

    def addNewApp(self, pkgname):
        if pkgname not in self.apps:
            self.apps[pkgname] = dict()
            self.apps[pkgname]["usage"] = defaultdict(int)
            self.apps[pkgname]["user_list"] = defaultdict(list)
            self.apps[pkgname]["pub_indexes"] = set()
            self.apps[pkgname]["co_occurence"] = defaultdict(lambda: {"static": 0, "logical": 0} )

    def getUnknownAppInfo(self, pkgname):
        if (pkgname in self.app_info):
            inf = self.app_info[pkgname].copy()
            if (inf["title"] != pkgname):
                inf["short_description"] = "(" + inf["title"] + ") " + inf["short_description"]
                inf["description"] = "(" + inf["title"] + ") " + inf["description"]
                inf["title"] = pkgname
        else:
            inf =  {
               "title" : pkgname,
               "description" : "unknown",
               "short_description" : "unknown",
               "image" : "unknown.jpg",
               "version" : "",
               "publications" : 0 }
        return inf

    def writeNewApp(self, apptitle):
        thisappinfo = self.getUnknownAppInfo(apptitle)

        id = self.db.application.save(thisappinfo)
        self.db.usage.save({ "application": id, "daily" : [], "weekly" : [], "monthly" : [] })
        self.db.users_usage.save({ "application": id, "daily" : [], "weekly" : [], "monthly" : [] })
        self.db.user_list.save({ "application": id, "users" : [] })
        self.db.co_occurence.save({ "application": id, "links" : [] })
        self.appIds[id] = thisappinfo["title"]
        return id

    def translateAppname(self, appname):
        return appname  
        #self.app_info.get(appname, {"title": appname})["title"]

    def registerPacket(self, packet):
        "Update in-memory data structure with incoming packet"

        with usageCacheLock:
            self.dirty = True
            today = epoch2date(packet["startEpoch"])
            for pkgT in packet["pkgT"]:
               pkgname = self.translateAppname(pkgT.split("/")[0])
               if isinstance(pkgname, dict):
                    print "pkgname is a dict!", pkgname
                    pdb.set_trace()
               self.addNewApp(pkgname)
               self.apps[pkgname]["usage"][dayOf(today)] = \
                    self.apps[pkgname]["usage"].get(dayOf(today), 0) + 1
               self.apps[pkgname]["user_list"][dayOf(today)] = \
                    list(set(self.apps[pkgname]["user_list"].get(dayOf(today), []) + [packet["user"]]))

            # Fill in publications
            if (len(self.pub_indexes) > 0 and "account" in packet):
                ixs = self.pub_indexes.get(packet["account"], set())
                self.apps[pkgname]["pub_indexes"] = self.apps[pkgname]["pub_indexes"].union(ixs)
    
            # Fill in co-occurence
            roots = [self.translateAppname(p.split("/")[0]) for p in packet["pkgT"]]  #self.apps.keys()

            for pkgT in packet["pkgT"]:
                dependor = self.translateAppname(pkgT.split("/")[0])
                self.addNewApp(dependor)
                if isinstance(packet["pkgT"], dict):
                    deplist = packet["pkgT"][pkgT]
                    if (isinstance(deplist, list)):
                        links = [self.translateAppname(p.split("/")[0]) for p in deplist]
                    else:
                        links = [self.translateAppname(str(deplist).split("/")[0])]
                    if (len(links) > 0):
                        roots = [l for l in roots if l not in links]
                        for dependee in links:
                            if dependee in self.apps.keys() and dependee != dependor:
                                self.apps[dependor]["co_occurence"][dependee]["static"] += 1
                                self.update_max_co_use(self.apps[dependor]["co_occurence"][dependee])
            if (self.logicallyLinkRoots):
                for l1 in roots:
                    for l2 in roots:
                        if (l1 != l2):
                            try:
                                self.apps[l1]["co_occurence"][l2]["logical"] += 1
                            except:
                                pdb.set_trace()
                            self.update_max_co_use(self.apps[l1]["co_occurence"][l2])
    
            if ("weakPackDeps" in packet and isinstance(packet["weakPackDeps"], dict)):
                for weakdependor in packet["weakPackDeps"]:
                    if (isinstance(packet["weakPackDeps"][weakdependor], (list, dict))):
                        for weakdependee in packet["weakPackDeps"][weakdependor]:
                            if weakdependee == weakdependor:
                                pdb.set_trace()
                            self.apps[weakdependor]["co_occurence"][weakdependee]["logical"] += 1
                            self.update_max_co_use(self.apps[weakdependor]["co_occurence"][weakdependee])
                    else:
                        weakdependee = packet["weakPackDeps"][weakdependor]
                        if weakdependee == weakdependor:
                            pdb.set_trace()
                        self.apps[weakdependor]["co_occurence"][weakdependee]["logical"] += 1
                        self.update_max_co_use(self.apps[weakdependor]["co_occurence"][weakdependee])
    
    def saveToMongo(self):
        "Update database based on in-memory data structure"

        app_table = self.db.application
        with usageCacheLock:
	    for appname in self.apps:
                app = self.apps[appname]
                if "id" not in app:
                    app["id"] = self.writeNewApp(appname)

	    for appname in self.apps:
                app = self.apps[appname]
                id = app["id"] 
            
                # Save usage *counts*
                usageData = fillInDayWeekMonth(app["usage"], 0, lambda x,y: x+y, "x", "y")
                thisusage = self.db.usage.find_one({"application": id})
                thisusage["daily"] = usageData["daily"]
                thisusage["weekly"] = usageData["weekly"]
                thisusage["monthly"] = usageData["monthly"]
                app_usage = usageData["total"]
                self.db.usage.save(thisusage)

                # Save list of users.  We won't save the weekly/monthly sets, but we'll use them a few lines down
                #  to calculate weekly/monthly user counts
                userListData = fillInDayWeekMonth(app["user_list"], [], lambda x,y: list(set(x+y)), "date","users")
                thisuser_list = self.db.user_list.find_one({"application": id})
                thisuser_list["users"] =  [ {"date": item["date"], "users": list(item["users"])} for item in userListData["daily"] ]
                self.db.user_list.save(thisuser_list)

                # Calculate publication list
                if (len(self.pub_indexes) > 0 and len(app.get("pub_indexes",set()))>0):
                    publist = self.db.pub_list.find_one({"application": id})
                    if (publist is None):
                        publist = {"application": id}
                    publist["publications"] = [self.pub_list[i] for i in app["pub_indexes"]]
                    self.db.pub_list.save(publist)
                

                # Save counts of users.  We *do* need weekly/monthly here.
                thisusers = self.db.users_usage.find_one({"application": id})
                thisusers["daily"] = [{"x": i["date"], "y": len(i["users"])} for i in userListData["daily"]]
                thisusers["weekly"] = [{"x": i["date"], "y": len(i["users"])} for i in userListData["weekly"]]
                thisusers["monthly"] = [{"x": i["date"], "y": len(i["users"])} for i in userListData["monthly"]]
                self.db.users_usage.save(thisusers)
                app_users = len(userListData["total"])
               
                # Save application metadata.
		appRec = self.db.application.find_one({"_id": id})
                appRec["usage"] = app_usage
                appRec["usage_trend"] = sum([pt["y"] for pt in thisusage["daily"] if self.isTrending(pt["x"]) ])
                appRec["users"] = app_users
                if (len(app["pub_indexes"]) > 0):
                    appRec["publications"] = len(app["pub_indexes"])
                self.db.application.save(appRec)

                coocRec = self.db.co_occurence.find_one({"application": id})
                for k in app["co_occurence"]:
                    if id == self.apps[k]["id"]:
                        print "Here is where we ahve it"
                        pdb.set_trace()
                try:
                    coocRec["links"] = [{"app":self.apps[k]["id"], "co_uses":app["co_occurence"][k]} for k in app["co_occurence"]]
                except:
                    pdb.set_trace()
                self.db.co_occurence.save(coocRec)

            gs = self.db.global_stats.find_one()
            gs["max_co_uses"] = self.max_co_uses
            self.db.global_stats.save(gs)
            self.dirty = False

    def update_max_co_use(self, n):
        if n["static"] > self.max_co_uses["static"]:
            self.max_co_uses["static"] = n["static"];
        if n["logical"] > self.max_co_uses["logical"]:
            self.max_co_uses["logical"] = n["logical"];

    def isTrending(self, theDateYmd):
        return (self.today - ymd2date(theDateYmd)).days < 60


def pairlist2dict(pairlist, keyname, valname):
    return { p[keyname] : p[valname]  for p in pairlist }
    
def dict2pairlist(theDict, keyname, valname):
    return [{ keyname : key, valname : theDict[key]} for key in sorted(theDict.keys())]
        
def epoch2date(epoch):
    return datetime.datetime.fromtimestamp(float(epoch)).date()
    
def ymd2date(ymd): return dt.strptime(ymd, "%Y-%m-%d").date()

def date2ymd(dt): return dt.isoformat()

def dayOf(when):
    return when.isoformat()

def weekOf(when):
    return (when + datetime.timedelta(days=-when.weekday())).isoformat()

def monthOf(when):
    return date(when.year, when.month, 1).isoformat()

def fillInDayWeekMonth(dayhash, zero, accum, ix, value):
    delta = datetime.timedelta(days=1)
    start = ymd2date(min(dayhash.keys()))
    end = ymd2date(max(dayhash.keys()))
    daily = {k:v for (k,v) in dayhash.items()}
    weekly = {}
    monthly = {}
    total = zero
    day = start
    while day <= end:
        d = dayOf(day)
        w = weekOf(day)
        m = monthOf(day)
        if d not in daily:
            daily[d] = zero
        if w not in weekly:
            weekly[w] = zero
        if m not in monthly:
            monthly[m] = zero
        weekly[w] = accum(weekly[w], daily[d])
        monthly[m] = accum(monthly[m], daily[d])
        total = accum(total, daily[d])
        day += delta
    coll = {}
    coll["total"] = total
    coll["daily"] = dict2pairlist(daily, ix, value)
    coll["weekly"] = dict2pairlist(weekly, ix, value)
    coll["monthly"] = dict2pairlist(monthly, ix, value)
    return coll

# Used to exclude these R packages because they come by default: could do so in the future I guess...
#     defaultPkgs = ["stats","utils","base","R","methods","graphics","datasets","RJSONIO","grDevices","scimapClient", "scimapRegister"]
#
