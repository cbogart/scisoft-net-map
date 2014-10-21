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

def freshDb(c, dbname):
    c.drop_database(dbname)
    db = c[dbname]
    db.global_stats.save({"max_co_uses": { "static": 0, "logical": 0}, "max_publications": 0 })
    return db

class UsageCache:

    def __init__(self, dest, logicallyLinkLeaves):
        "Load a fresh database from mongo"

        self.logicallyLinkLeaves = logicallyLinkLeaves
        with usageCacheLock:
            self.today = datetime.date.today()
            self.db = dest
            self.apps = dict()
            self.dirty = False
            self.appIds = {}
            for app in dest.application.find():
                self.apps[app["title"]] = { 
                   "id": app["_id"],
                   "usage": {},
                   "user_list": {},
                   "co_occurence": {} 
                }
                self.appIds[app["_id"]] = app["title"]
           
            for a_usage in dest.usage.find():
                appname = self.appIds[a_usage["application"]]
                self.apps[appname]["usage"] = pairlist2dict(a_usage["daily"], "x", "y")
    
            for a_user_list in dest.user_list.find():
                appname = self.appIds[a_user_list["application"]]
                self.apps[appname]["user_list"] = pairlist2dict(a_user_list["daily"], "date", "items")
    
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
            self.apps[pkgname]["user_list"] = defaultdict(set)
            self.apps[pkgname]["co_occurence"] = defaultdict(lambda: {"static": 0, "logical": 0} )

    def writeNewApp(self, apptitle):
        appinfo = {}
        appinfo["title"] = apptitle
        appinfo["description"] = "unknown"
        appinfo["short_description"] = "unknown"
        appinfo["image"] = "unknown.jpg"
        appinfo["version"] = ""
        appinfo["publications"] = 0

        id = self.db.application.save(appinfo)
        self.db.usage.save({ "application": id, "daily" : [], "weekly" : [], "monthly" : [] })
        self.db.users_usage.save({ "application": id, "daily" : [], "weekly" : [], "monthly" : [] })
        self.db.user_list.save({ "application": id, "daily" : [], "weekly" : [], "monthly" : [] })
        self.db.co_occurence.save({ "application": id, "links" : [] })
        self.appIds[id] = appinfo["title"]
        return id

    def registerPacket(self, packet):
        "Update in-memory data structure with incoming packet"

        with usageCacheLock:
            self.dirty = True
            today = epoch2date(packet["startEpoch"])
            for pkgT in packet["pkgT"]:
               pkgname = pkgT.split("/")[0]
               self.addNewApp(pkgname)
               self.apps[pkgname]["usage"][dayOf(today)] += 1
               self.apps[pkgname]["user_list"][dayOf(today)].add(packet["user"])
    
            # Fill in co-occurence
            leaves = [p.split("/")[0] for p in packet["pkgT"].keys()]  #self.apps.keys()
            roots = []
            #if (packet["pkgT"] != {packet["exec"]: []} and packet["pkgT"] != {}):
                #pdb.set_trace()
            for pkgT in packet["pkgT"]:
                dependor = pkgT.split("/")[0]
                self.addNewApp(dependor)
                if isinstance(packet["pkgT"], dict):
                    links = [p.split("/")[0] for p in packet["pkgT"][pkgT]]
                    if (isinstance(links, list) and len(links) > 0):
                        leaves = [l for l in leaves if l not in links]
                        for dependee in links:
                            if dependee in self.apps.keys() and dependee != dependor:
                                self.apps[dependor]["co_occurence"][dependee]["static"] += 1
                                self.update_max_co_use(self.apps[dependor]["co_occurence"][dependee])
                    elif (isinstance(links, list) and len(links) == 0):
                        roots.append(dependor)
                    elif links in self.apps.keys():
                        leaves = [l for l in leaves if l is not links]
                        if (dependor != links):
                            self.apps[dependor]["co_occurence"][links]["static"] += 1
                            self.update_max_co_use(self.apps[dependor]["co_occurence"][links])
                    else:
                        print "pkgT", pkgT, " points to a ", links
                        #pdb.set_trace()
                else:
                   print "Not a dict"
                   #pdb.set_trace()
            if (self.logicallyLinkLeaves):
                for l1 in leaves:
                    for l2 in leaves:
                        if (l1 != l2):
                            #pdb.set_trace()
                            try:
                                self.apps[l1]["co_occurence"][l2]["logical"] += 1
                            except:
                                pdb.set_trace()
                            self.update_max_co_use(self.apps[l1]["co_occurence"][l2])
    
            if ("weakPackDeps" in packet and isinstance(packet["weakPackDeps"], dict)):
                for weakdependor in packet["weakPackDeps"]:
                    if (isinstance(packet["weakPackDeps"][weakdependor], (list, dict))):
                        for weakdependee in packet["weakPackDeps"][weakdependor]:
                            #pdb.set_trace()
                            self.apps[weakdependor]["co_occurence"][weakdependee]["logical"] += 1
                            self.update_max_co_use(self.apps[weakdependor]["co_occurence"][weakdependee])
                    else:
                        weakdependee = packet["weakPackDeps"][weakdependor]
                        #pdb.set_trace()
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

                # Save lists of users.  Technically we don't need the weekly/monthly lists
                userListData = fillInDayWeekMonth(app["user_list"], set(), lambda x,y: x.union(y), "date","items")
                thisuser_list = self.db.user_list.find_one({"application": id})
                thisuser_list["daily"] = [{"date": i["date"], "items": list(i["items"])} for i in userListData["daily"]]
                thisuser_list["weekly"] = [{"date": i["date"], "items": list(i["items"])} for i in userListData["weekly"]]
                thisuser_list["monthly"] = [{"date": i["date"], "items": list(i["items"])} for i in userListData["monthly"]]
                self.db.user_list.save(thisuser_list)

                # Save counts of users.  We *do* need weekly/monthly here.
                thisusers = self.db.users_usage.find_one({"application": id})
                thisusers["daily"] = [{"x": i["date"], "y": len(i["items"])} for i in userListData["daily"]]
                thisusers["weekly"] = [{"x": i["date"], "y": len(i["items"])} for i in userListData["weekly"]]
                thisusers["monthly"] = [{"x": i["date"], "y": len(i["items"])} for i in userListData["monthly"]]
                self.db.users_usage.save(thisusers)
                app_users = len(userListData["total"])
               
                # Save application metadata.
		appRec = self.db.application.find_one({"_id": id})
                appRec["usage"] = app_usage
                appRec["usage_trend"] = sum([pt["y"] for pt in thisusage["daily"] if self.isTrending(pt["x"]) ])
                appRec["users"] = app_users
                self.db.application.save(appRec)

                coocRec = self.db.co_occurence.find_one({"application": id})
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
        else:
            daily[d] = daily[d]
        if w not in weekly:
            weekly[w] = zero
        else:
            weekly[w] = accum(weekly[w], daily[d])
        if m not in monthly:
            monthly[m] = zero
        else:
            monthly[m] = accum(monthly[m], daily[d])
        total = accum(total, daily[d])
        day += delta
    coll = {}
    coll["total"] = total
    coll["daily"] = dict2pairlist(daily, ix, value)
    coll["weekly"] = dict2pairlist(weekly, ix, value)
    coll["monthly"] = dict2pairlist(monthly, ix, value)
    return coll

# ----- Junk below this line
'''
def getUnknownAppInfo(pkgname):
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

class Apps:
    def __init__(self, c, dest):
       self.c = c
       self.dest = dest
       self.idtable = {}

    def newjob(self):
       self.idtable = {}

    def addApp(self, name):
       appinfo = getUnknownAppInfo(name)

    def getId(self, name):
       if name not in self.idtable:
           self.addApp(name)
       return self.idtable[name]
       
    def allIdsForThisJob(self):
       return self.idtable.values()

    
class Dependencies:
    def __init__(self, dest):
        self.ddict = dict()
        for cooc in dest.co_occurence.find():
            self.ddict[cooc["application"]] = pairlist2dict(cooc["links"], "app", "co_uses")
        self.max_co_uses = {"static": 0, "logical": 0}

    def update_max_co_use(self, n):
        if n["static"] > self.max_co_uses["static"]:
            self.max_co_uses["static"] = n["static"];
        if n["logical"] > self.max_co_uses["logical"]:
            self.max_co_uses["logical"] = n["logical"];
    
    def updateCooc(self, dest):
        for id in self.ddict:
           cooc = dest.co_occurence.find_one({"application": id})
           cooc["links"] = dict2pairlist(self.ddict[id], "app", "co_uses")
           dest.co_occurence.save(cooc)
        
    def ensureCreated(self, dependor, dependee):
        if dependor not in self.ddict:
            self.ddict[dependor] = dict()
        if dependee not in self.ddict[dependor]:
            self.ddict[dependor][dependee] = {"static": 0, "logical": 0} 

    def incStatic(self, dependor, dependee):
        self.ensureCreated(dependor, dependee)
        self.ddict[dependor][dependee]["static"] += 1
        self.update_max_co_use(self.ddict[dependor][dependee])
        print "Static: ", dependor, dependee

    def incLogical(self, dependor, dependee):
        self.ensureCreated(dependor, dependee)
        self.ddict[dependor][dependee]["logical"] += 1
        self.update_max_co_use(self.ddict[dependor][dependee])
        print "Logical: ", dependor, dependee
    


            
def updateData(datapoints, epoch, datef, default, xname, yname, incf):
    """ Update a stream of (x,y) points in the database using an increment function.  
    
    Returns: the output of that function
    
    datapoints: a list of dictionaries of x,y, where x is a date, and y is a count or list of users
    epoch: a date in unix format
    datef: a function converting a date to a YYYY-MM-DD, rounded to some unit (day, month, or week)
    default: the default value of a y coordinate
    xname: the name of the x coordinate (the date)
    yname: the name of the y coordinate (usually a count, but could be a list of users)
    incf: the function to apply to the data item, when found
    """
    
    # Find or create the appropriate datapoint
    matches = [dp for dp in datapoints if datef(epoch2date(epoch)) == dp[xname]]
    if len(matches) == 0:
        newone = { xname : datef(epoch2date(epoch)), yname : default }
        datapoints.append(newone)
        matches = [newone]
        
    # Update it
    matches[0][yname] = incf(matches[0][yname])
     
    return matches[0][yname]
    
defaultPkgs = ["stats","utils","base","R","methods","graphics","datasets","RJSONIO","grDevices","scimapClient", "scimapRegister"]
    
appstore = None

def recalcApps(c, dest):
    global appstore
    if (appstore is None): appstore=Apps(c,dest)
    appstore.newjob()

    for app in dest.application.find():
        u = dest.usage.find_one({"application": app["_id"]})
        uls = dest.user_list.find_one({"application": id})
        uu = dest.users_usage.find_one({"application": id})
        fillInZeroes(u)
        fillInZeroes(uu)
        app["usage"] = sum([pt["y"] for pt in u["monthly"]])
        app["usage_trend"] = sum([pt["y"] for pt in u["daily"] if isTrending(pt["x"]) ])
        app["users"] = len(set([user for item in u["monthly"] for user in item["users"]]))
        dest.usage.save(u)
        dest.user_list.save(uls)
        dest.users.save(uu)
        dest.application.save(app)
    

def addOne(c, dest, rawrec, postponeCalc = False):
    global appstore
    if (appstore is None): appstore=Apps(c,dest)
    appstore.newjob()
    #execid = appstore.getId(rawrec["exec"])

    for pkgT in rawrec["pkgT"]:
       pkgname = pkgT.split("/")[0]
       if pkgname not in defaultPkgs:
           appstore.addApp(pkgname)

    for id in appstore.allIdsForThisJob():
        app = dest.application.find_one({"_id": id})
        
        u = dest.usage.find_one({"application": id})
        updateData(u["daily"], rawrec["startEpoch"], dayOf, 0, "x", "y", (lambda (i):  i+1 )  )
        updateData(u["weekly"], rawrec["startEpoch"], weekOf, 0, "x", "y", lambda (i) :  i+1    )
        updateData(u["monthly"], rawrec["startEpoch"], monthOf, 0, "x", "y", lambda (i) :  i+1  )
        if (not postponeCalc): 
            fillInZeroes(u)
        dest.usage.save(u)

        if (not postponeCalc): 
            app["usage"] = sum([pt["y"] for pt in u["monthly"]])
            app["usage_trend"] = sum([pt["y"] for pt in u["daily"] if isTrending(pt["x"]) ])
        
        uls = dest.user_list.find_one({"application": id})
        users_today = updateData(uls["daily"], rawrec["startEpoch"], dayOf, [], "date", "users", lambda (ul) :  list(set(ul + [rawrec["user"]])) )
        users_thisweek = updateData(uls["weekly"], rawrec["startEpoch"], weekOf, [], "date", "users", lambda (ul) :  list(set(ul + [rawrec["user"]]))  )
        users_thismonth = updateData(uls["monthly"], rawrec["startEpoch"], monthOf, [], "date", "users", lambda (ul) :  list(set(ul + [rawrec["user"]]))  )
        dest.user_list.save(uls)

        if (not postponeCalc): 
            app["users"] = len(set([user for item in uls["monthly"] for user in item["users"]]))
        dest.application.save(app)
        
        uu = dest.users_usage.find_one({"application": id})
        updateData(uu["daily"], rawrec["startEpoch"], dayOf,  0, "x", "y", lambda (u2) :  len(users_today)   )
        updateData(uu["weekly"], rawrec["startEpoch"], weekOf,  0, "x", "y", lambda (u2) :  len(users_thisweek)  )
        updateData(uu["monthly"], rawrec["startEpoch"], monthOf, 0, "x", "y", lambda (u2) :  len(users_thismonth)   )
        if (not postponeCalc): 
            fillInZeroes(uu)
        dest.users_usage.save(uu)
        
        # Disabled code from previous version: this fully connects all packages from the same job
        if (isinstance(rawrec["pkgT"], list) and 1==0):   
            cooc = dest.co_occurence.find_one({"application": id})
            ptrs = pairlist2dict(cooc["links"], "app", "co_uses")
            for id2 in appstore.allIdsForThisJob():
                if (id != id2):
                    if id2 not in ptrs:
                        ptrs[id2] = 5
            cooc["links"] = dict2pairlist(ptrs, "app", "co_uses")
            dest.co_occurence.save(cooc)
            
    deps = Dependencies(dest)
    if (isinstance(rawrec["pkgT"], dict)):  
        roots = []   
        leaves = appstore.idtable.keys()
        for pkgT in rawrec["pkgT"]:
            dependor = pkgT.split("/")[0]
            appstore.addApp(dependor)
            if dependor in appstore.idtable:
                links = rawrec["pkgT"][pkgT]
                if (isinstance(links, list) and len(links) > 0):
                    leaves = [l for l in leaves if l not in links]
                    for dependee in links:
                        if dependee in appstore.idtable:
                            deps.incStatic(appstore.getId(dependor), appstore.getId(dependee))
                elif (isinstance(links, list) and len(links) == 0):
                    roots.append(appstore.getId(dependor))
                elif links in appstore.idtable:
                    leaves = [l for l in leaves if l is not links]
                    deps.incStatic(appstore.getId(dependor), appstore.getId(links))
        leaves = [appstore.idtable[l] for l in leaves]
        for l1 in leaves:
            for l2 in leaves:
                if (l1 != l2):
                    deps.incLogical(l1, l2)
                    print("Found a logical link between ", l1, " and ", l2)

    if (isinstance(rawrec["weakPackDeps"], dict)):
        for weakdependor in rawrec["weakPackDeps"]:
            for weakdependee in rawrec["weakPackDeps"][weakdependor]:
                deps.incLogical(appstore.getId(weakdependor), appstore.getId(weakdependee))

    deps.updateCooc(dest)

    oldStats = dest.global_stats.find_one()
    if (oldStats == None):
        oldStats = { "max_co_uses": deps.max_co_uses, "max_publications": 0 }
    else:
        oldStats["max_co_uses"] = deps.max_co_uses
    dest.global_stats.save(oldStats)
                
        
if __name__ == "__main__":
    c = Connection()
    c.drop_database("snm-r")
    raw = c["snm-raw-records"]["scimapInfo"]
    dest = c["snm-r"]
    for rawrec in raw.find():
        addOne(c, dest, rawrec, postponeCalc = True)
    recalcApps(c, dest)
    
''' 
