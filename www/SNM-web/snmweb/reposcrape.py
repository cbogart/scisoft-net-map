import sqlite3
import pdb
import json
from collections import defaultdict
import datetime

def calcDependencyClosure(thesedepslist, depdictpkg2list):
    closuresDone = False
    closuresCycle = 0
    newdeps = { dep: depdictpkg2list.get(dep,[]) for dep in thesedepslist }
    while(not closuresDone):
        closuresDone = True
        closuresCycle += 1
        alllhs = set(newdeps.keys())
        allrhs = set([d2 for d1 in newdeps for d2 in newdeps[d1]])
        if len(allrhs) > len(alllhs):
            newdeps = dict(newdeps.items() + \
                  [(r, depdictpkg2list.get(r,[])) for r in allrhs])
            closuresDone = False
    return newdeps

assert calcDependencyClosure(["a", "b", "c"], { "a" : ["b", "d"] })== {"a": ["b", "d"], "b": [], "c": [] }, \
        calcDependencyClosure(["a", "b", "c"], { "a" : ["b", "d"] })

def getConnection(dbname):
    # Open the database
    conn = sqlite3.connect(dbname)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma short_column_names=OFF;");
    conn.execute("pragma full_column_names=ON;");
    return conn

def iso2epoch(dt):
    return datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S").strftime("%s")

class RepoScrape:
    def __init__(self, dbname):
        self.db = getConnection(dbname)
        
    def transferUsageDetails(self):
       uses = self.db.execute("select gitprojects.*, group_concat(distinct(package_name)) deps from gitprojects " +\
                   " left join gitimports on gitprojects.id=gitimports.project_id where gitprojects.cb_last_scan > 0 " +\
                   " and error == '' group by gitprojects.id having deps!='';");
       referers = []
       for use in uses:
           ref = {
               "url" : use["gitprojects.url"],
               "name": use["gitprojects.name"],
               "description": use["gitprojects.description"],
               "created_at": use["gitprojects.created_at"],
               "cb_last_scan": use["gitprojects.cb_last_scan"],
               "pushed_at": use["gitprojects.pushed_at"],
               "watchers_count": use["gitprojects.watchers_count"],
               "stargazers_count": use["gitprojects.stargazers_count"],
               "forks_count": use["gitprojects.forks_count"],
               "dependencies": use["deps"].split(",")
           }
           referers.append(ref)
       return referers

    def makeAppInfo(self):
       """Dump info from database into appinfo.R.json"""
       packages = self.db.execute("select * from packages")      

        # prefer cran to bioc to github
       self.appinfo = {}
       self.deps = {}

       oldappinfo = json.loads(
          open("../../data/appinfo.R.handedited.json", "r").read())

       for pack in packages:
           name = pack["packages.name"]
           self.appinfo[name] = oldappinfo.get(name, { "image": "unknown.jpg", "publications": 0})
           self.appinfo[name]["website"]= pack["packages.url"]
           self.appinfo[name]["repository"]= pack["packages.repository"]
           self.appinfo[name]["description"]= pack["packages.description"]
           self.appinfo[name]["title"]= pack["packages.title"]
           self.appinfo[name]["short_description"]=pack["packages.title"]
           self.appinfo[name]["match"]=[ name ]
           self.deps[name]= []

       deps = self.db.execute("select * from staticdeps")
       for dep in deps:
           self.deps[dep["staticdeps.package_name"]].append(dep["staticdeps.depends_on"])

    def writeAppInfo(self, appInfoFileName):
       with open(appInfoFileName, "w") as f: 
           f.write(json.dumps(self.appinfo, indent=4))

    def getPureGitDailyImportCount(self):   # REMOVE ME
       """package -> day -> number"""
       refs = self.db.execute("select package_name name, substr(pushed_at,0,11) dt, id " + \
           "from gitimports left join gitprojects on id=project_id group by name, dt, id");
       counts = defaultdict(lambda: defaultdict(int))
       for r in refs:
           counts[r["name"]][r["dt"]] += 1
       return counts


    def getGitCoOccurence(self):
       """package->package->number"""
       if (not hasattr(self, 'deps')):  
           self.makeAppInfo()
       refs = self.db.execute("select project_id, group_concat(distinct(package_name)) deps, " + \
               "substr(pushed_at,0,11) dt  from " + \
               "gitimports left join gitprojects on id=project_id group by project_id");
       cocounts = defaultdict(lambda: defaultdict(lambda: ("", 0)))
       counts = defaultdict(lambda: defaultdict(int))
       for r in refs:
           deps = r["deps"].split(",")
           alldeps = calcDependencyClosure(deps, self.deps)
           alldepscomplete = set(alldeps.keys() + [d for i in alldeps for d in alldeps[i]])
           for d1 in alldepscomplete:
               counts[d1][r["dt"]] += 1
               for d2 in alldepscomplete:
                   if (d1 != d2):
                       if d2 in alldeps.get(d1, []):   linktype = "upstream"
                       elif d1 in alldeps.get(d2, []): linktype = "downstream"
                       else:                   linktype = "usedwith"
                       cocounts[d1][d2] = (linktype, cocounts[d1][d2][1]+1)
       return (counts, cocounts)

    def getPureGitCoOccurrence(self):   # REMOVE ME
       """package->package->number"""

       refs = self.db.execute("select impA.package_name pkgA, impB.package_name pkgB, count(distinct(impA.project_id)) k from " +\
          "gitimports impA left join gitimports impB on impA.project_id=impB.project_id and " +\
          "impA.package_name != impB.package_name group by pkgA, pkgB")
       counts = defaultdict(lambda: defaultdict(int))
       for r in refs:
           counts[r["pkgA"]][r["pkgB"]] = int(r["k"])
       return counts

    def getGitCounts(self):
       """(lastgitproj, numgitprojs, numscraped)"""
       counts = self.db.execute('select max(pushed_at) lastgitproj, count(*) numgitprojs, ' + \
            'count(pushed_at) numscraped from gitprojects;');
       row = counts.next()
      
       return (iso2epoch(row["lastgitproj"]), int(row["numgitprojs"]), int(row["numscraped"]))

#
#  To do: is it OK that getGitDailyImportCount skips days?
#  To do: is it OK that getGitCoOccurrence does not fill in static dependencies?
#
#  To do: implement a finer-grained notion of 'uses':
#
#To identify distinct "uses"
#   - a "use" is a user + name + path ending in a directory.  Path might be empty
#   - identify all paths associated with descriptions, and put in a table
#   - if a file exactly matches a path, and NOT a description file, skip.
#   - if a file exactly matches a path and IS a description file, count its refs, project = the path
#   - if a file is an extension of an existing path, ignore the file
#   - if a file is a subpath of an existing path, or a completely new path, project = null path

