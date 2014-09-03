#!/usr/bin/python
#
# Author:
#  Chris Bogart
#
# Original record in collection scimapInfo is:
#
#{ "_id" : ObjectId("53ff48b09808db2cb61f07fe"), "account" : "0956680526176432635668900", 
# "exec" : "source, testRun.R", 
# "startEpoch" : "1409239802", 
# "jobID" : "09566805261764326356689001409239802", 
# "platform" : { "hardware" : "x86_64", "version" : "13.3.0", "system" : "Darwin" }, 
# "pkgT" : [  "GenomicRanges/1.16.4",     "GenomeInfoDb/1.0.2",   "IRanges/1.22.10",  
#             "BiocGenerics/0.10.0",  "parallel/3.1.1",   "scimapClient/0.1.0",   
#             "RJSONIO/1.3.0",    "httr/0.4",     "stats/3.1.1",  "graphics/3.1.1",   
#             "grDevices/3.1.1",  "utils/3.1.1",  "datasets/3.1.1",   "methods/3.1.1",    
#             "base/3.1.1" ], 
# "user" : "0956680526176432635668900", 
# "startTime" : "Thu Aug 28 11:30:02 2014" }
#
# Version 2:
#
#{ "_id" : ObjectId("53ff48b09808db2cb61f07fe"), "account" : "0956680526176432635668900", 
# "exec" : "source, testRun.R", 
# "startEpoch" : "1409239802", 
# "scimapInfoVersion" : 2,
# "jobID" : "09566805261764326356689001409239802", 
# "platform" : { "hardware" : "x86_64", "version" : "13.3.0", "system" : "Darwin" }, 
# "pkgT" : {  "GenomicRanges/1.16.4" : ["GenomeInfoDb", "stats", "graphics"],     
#             "GenomeInfoDb/1.0.2" : "parallel",
#             "parallel/3.1.1" : [],
#             . . . }     # NB: may have list, empty list [], or string singletons 
#                         # This inconsistency is awkward in python, but more consistent with R's array model
# "user" : "0956680526176432635668900", 
# "startTime" : "Thu Aug 28 11:30:02 2014" }
# New records should be:
#
# application
# co_occurence
# usage
# users_usage
#

from pymongo import MongoClient, Connection
import json
from collections import defaultdict
from datetime import date, timedelta
from datetime import datetime as dt
import datetime
import pdb
import json
    
appf = open("appinfo.json", "r")
apps = json.loads(appf.read())

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

def addAppUnknown(c, dest, appname):
    return addApp(c,dest, getUnknownAppInfo(appname))
           
def addApp(c, dest, appinfo):
    finding = dest.application.find_one({"title": appinfo["title"]})
    if finding:
        return finding["_id"]
    else:
        id = dest.application.save(appinfo)
        dest.usage.save({ "application": id, "daily" : [], "weekly" : [], "monthly" : [] })
        dest.users_usage.save({ "application": id, "daily" : [], "weekly" : [], "monthly" : [] })
        dest.user_list.save({ "application": id, "daily" : [], "weekly" : [], "monthly" : [] })
        dest.co_occurence.save({ "application": id, "links" : [] })
        return id

def epoch2date(epoch):
    return datetime.datetime.fromtimestamp(float(epoch)).date()
    
def isTrending(theDateYmd):
    return (datetime.date.today() - ymd2date(theDateYmd)).days < 60

def ymd2date(ymd): return dt.strptime(ymd, "%Y-%m-%d").date()

def date2ymd(dt): return dt.isoformat()

def dayOf(when):
    return when.isoformat()

def weekOf(when):
    return (when + datetime.timedelta(days=-when.weekday())).isoformat()

def monthOf(when):
    return date(when.year, when.month, 1).isoformat()
    
def cooc2ddict(dest):
    ddict = dict()
    for cooc in dest.co_occurence.find():
        ddict[cooc["application"]] = pairlist2dict(cooc["links"], "app", "power")
    return ddict
    
def ddict2cooc(dest, ddict):
    for id in ddict:
       cooc = dest.co_occurence.find_one({"application": id})
       cooc["links"] = dict2pairlist(ddict[id], "app", "power")
       dest.co_occurence.save(cooc)
        
def pairlist2dict(pairlist, keyname, valname):
    return { p[keyname] : p[valname]  for p in pairlist }
    
def dict2pairlist(theDict, keyname, valname):
    return [{ keyname : key, valname : theDict[key]} for key in sorted(theDict.keys())]
        
def fillInZeroes(coll):
    today = datetime.date.today()
    delta = datetime.timedelta(days=1)
    daily = pairlist2dict(coll["daily"], "x", "y")
    weekly = pairlist2dict(coll["weekly"], "x", "y")
    monthly = pairlist2dict(coll["monthly"], "x", "y")
    start = ymd2date(min(daily.keys()))
    day = start
    while day <= today:
        if dayOf(day) not in daily:
            daily[dayOf(day)] = 0
        if weekOf(day) not in weekly:
            weekly[weekOf(day)] = 0
        if monthOf(day) not in monthly:
            monthly[monthOf(day)] = 0
        day += delta
    coll["daily"] = dict2pairlist(daily, "x", "y")
    coll["weekly"] = dict2pairlist(weekly, "x", "y")
    coll["monthly"] = dict2pairlist(monthly, "x", "y")
            
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
    
def addOne(c, dest, rawrec):
    idtable = dict()
    #execid = addAppUnknown(c,dest, rawrec["exec"])
    #idtable[rawrec["exec"]] = execid
    depids = []
    inf = {}
    for pkgT in rawrec["pkgT"]:
       pkgname = pkgT.split("/")[0]
       if pkgname not in defaultPkgs:
           id = addAppUnknown(c, dest, pkgname)
           depids.append(id)
           idtable[pkgname] = id
    allids = depids #+ [execid]
    for id in allids:
        app = dest.application.find_one({"_id": id})
        
        u = dest.usage.find_one({"application": id})
        updateData(u["daily"], rawrec["startEpoch"], dayOf, 0, "x", "y", (lambda (i):  i+1 )  )
        updateData(u["weekly"], rawrec["startEpoch"], weekOf, 0, "x", "y", lambda (i) :  i+1    )
        updateData(u["monthly"], rawrec["startEpoch"], monthOf, 0, "x", "y", lambda (i) :  i+1  )
        fillInZeroes(u)
        dest.usage.save(u)
        app["usage"] = sum([pt["y"] for pt in u["monthly"]])
        app["usage_trend"] = sum([pt["y"] for pt in u["daily"] if isTrending(pt["x"]) ])
        
        u = dest.user_list.find_one({"application": id})
        users_today = updateData(u["daily"], rawrec["startEpoch"], dayOf, [], "date", "users", lambda (ul) :  list(set(ul + [rawrec["user"]])) )
        users_thisweek = updateData(u["weekly"], rawrec["startEpoch"], weekOf, [], "date", "users", lambda (ul) :  list(set(ul + [rawrec["user"]]))  )
        users_thismonth = updateData(u["monthly"], rawrec["startEpoch"], monthOf, [], "date", "users", lambda (ul) :  list(set(ul + [rawrec["user"]]))  )
        dest.user_list.save(u)
        app["users"] = len(set([user for item in u["monthly"] for user in item["users"]]))
        dest.application.save(app)
        
        uu = dest.users_usage.find_one({"application": id})
        updateData(uu["daily"], rawrec["startEpoch"], dayOf,  0, "x", "y", lambda (u2) :  len(users_today)   )
        updateData(uu["weekly"], rawrec["startEpoch"], weekOf,  0, "x", "y", lambda (u2) :  len(users_thisweek)  )
        updateData(uu["monthly"], rawrec["startEpoch"], monthOf, 0, "x", "y", lambda (u2) :  len(users_thismonth)   )
        fillInZeroes(uu)
        dest.users_usage.save(uu)
        
        if (isinstance(rawrec["pkgT"], list)):
            cooc = dest.co_occurence.find_one({"application": id})
            ptrs = pairlist2dict(cooc["links"], "app", "power")
            for id2 in allids:
                if (id != id2):
                    if id2 not in ptrs:
                        ptrs[id2] = 5
            cooc["links"] = dict2pairlist(ptrs, "app", "power")
            dest.co_occurence.save(cooc)
            
    if (isinstance(rawrec["pkgT"], dict)):  
        ddict = cooc2ddict(dest)
        leaves = []   
        for pkgT in rawrec["pkgT"]:
            dependor = pkgT.split("/")[0]
            if dependor in idtable:
                ddict[idtable[dependor]] = {}
                links = rawrec["pkgT"][pkgT]
                if (isinstance(links, list) and len(links) > 0):
                    for dependee in links:
                        if dependee in idtable:
                            ddict[idtable[dependor]][idtable[dependee]] = 5
                elif (isinstance(links, list) and len(links) == 0):
                    leaves.append(idtable[dependor])
                elif links in idtable:
                    ddict[idtable[dependor]][idtable[links]] = 5
        for l1 in leaves:
            for l2 in leaves:
                if (l1 != l2):
                    ddict[l1][l2] = 5 
        ddict2cooc(dest, ddict)
                
        
if __name__ == "__main__":
    c = Connection()
    c.drop_database("snm-r")
    raw = c["snm-raw-records"]["scimapInfo"]
    dest = c["snm-r"]
    for rawrec in raw.find():
        addOne(c, dest, rawrec)
        
