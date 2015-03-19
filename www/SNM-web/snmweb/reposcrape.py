import sqlite3
import pdb
import json
import re
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

legalimport = re.compile("^[a-zA-Z_0-9\._]+$")

class RepoScrape:
    def __init__(self, dbname):
        self.db = getConnection(dbname)
        
    def loadCitationDetails(self):
        """Load a list of citations to be placed in database"""
        cites = self.db.execute("select * from citations where length(doi)>0 " +\
                                "or length(scopus_id)>0 or canonical != 'synthetic';");
        citations = defaultdict(list)
        for cite in cites:
            if cite["citations.title"].startswith("Error:"):
                continue
            citations[cite["citations.package_name"]].append({
                "citation_text": cite["citations.citation"],
                "year": cite["citations.year"],
                "doi_given": cite["citations.doi_given"],
                "author": cite["citations.author"],
                "title": cite["citations.title"],
                "doi": cite["citations.doi"],
                "scopus_citedby_count": cite["citations.scopus_citedby_count"],
                "scopus_url": cite["citations.scopus_url"],
                "canonical": cite["citations.canonical"]==1})
        return citations
    
    def transferUsageDetails(self):
        """Load a list-of-dicts describing all R github projects"""
        uses = self.db.execute("select gitprojects.*, group_concat(distinct(package_name)) deps from gitprojects " +\
                   " left join gitimports on gitprojects.id=gitimports.project_id where gitprojects.cb_last_scan > 0 " +\
                   " and error == '' group by gitprojects.id having deps!='';");
        referers = []
        for use in uses:
            deps = filter(legalimport.match, use["deps"].split(","))
            alldeps = calcDependencyClosure(deps, self.deps)
            alldepscomplete = sorted(list(set(alldeps.keys() + [d for i in alldeps for d in alldeps[i]])))

            if "\n" in use["gitprojects.name"]:
                print "FAIL RIGHT HERE LINE 50"
            ref = {
               "url" : use["gitprojects.url"],
               "name": use["gitprojects.name"],
               "owner": use["gitprojects.owner"],
               "description": use["gitprojects.description"],
               "created_at": use["gitprojects.created_at"],
               "cb_last_scan": use["gitprojects.cb_last_scan"],
               "pushed_at": use["gitprojects.pushed_at"],
               "watchers_count": use["gitprojects.watchers_count"],
               "stargazers_count": use["gitprojects.stargazers_count"],
               "forks_count": use["gitprojects.forks_count"],
               "dependencies": alldepscomplete  #filter(legalimport.match, use["deps"].split(","))
            }
            referers.append(ref)
        return referers

    def makeAppInfo(self):
       """Dump info from database into appinfo.R.json"""
       packages = self.db.execute("select packages.*, group_concat(distinct(tags.tag)) views from packages left join tags on packages.name = tags.package_name group by packages.name;")

        # prefer cran to bioc to github
       self.appinfo = {}
       self.deps = {}

       oldappinfo = json.loads(
          open("../../data/appinfo.R.handedited.json", "r").read())

       for pack in packages:
           name = pack["packages.name"]
           if "\n" in name:
               print "FAIL RIGHT HERE line 78"
           self.appinfo[name] = oldappinfo.get(name, { "image": "unknown.jpg", "publications": 0})
           self.appinfo[name]["website"]= pack["packages.url"]
           self.appinfo[name]["repository"]= pack["packages.repository"]
           self.appinfo[name]["description"]= pack["packages.description"]
           self.appinfo[name]["title"]= pack["packages.title"]
           self.appinfo[name]["short_description"]=pack["packages.title"]
           self.appinfo[name]["match"]=[ name ]
           self.appinfo[name]["views"]=pack["views"].split(",") if pack["views"] is not None else []
           self.deps[name]= []

       deps = self.db.execute("select * from staticdeps")
       for dep in deps:
           if "\n" in dep["staticdeps.package_name"] or "\n" in dep["staticdeps.depends_on"]:
                print "FAIL RIGHT HERE line 90"
           self.deps[dep["staticdeps.package_name"]].append(dep["staticdeps.depends_on"])

    def writeAppInfo(self, appInfoFileName):
       with open(appInfoFileName, "w") as f: 
           f.write(json.dumps(self.appinfo, indent=4))

    def getGitCoOccurence(self):
       """How many times did every pair of packages appear together as imports in github packages?
       
       returns: dict(dict(int)), that is, package->package->count"""
       
       if (not hasattr(self, 'deps')):  
           self.makeAppInfo()
       refs = self.db.execute("select project_id, group_concat(distinct(package_name)) deps, " + \
               "substr(pushed_at,0,11) lastcommit  from " + \
               "gitimports left join gitprojects on id=project_id group by project_id");
       cocounts = defaultdict(lambda: defaultdict(lambda: ("", 0)))
       counts = defaultdict(lambda: defaultdict(int))
       for r in refs:
           deps = filter(legalimport.match, (r["deps"] or "").split(","))
           alldeps = calcDependencyClosure(deps, self.deps)
           alldepscomplete = set(alldeps.keys() + [d for i in alldeps for d in alldeps[i]])
           for d1 in alldepscomplete:
               counts[d1][r["lastcommit"]] += 1
               for d2 in alldepscomplete:
                   if (d1 != d2):
                       if d2 in alldeps.get(d1, []):   linktype = "upstream"
                       elif d1 in alldeps.get(d2, []): linktype = "downstream"
                       else:                   linktype = "usedwith"
                       cocounts[d1][d2] = (linktype, cocounts[d1][d2][1]+1)
       return (counts, cocounts)

    def getGitCounts(self):
       """Overall statistics about git projects surveyed
       
       returns: (lastgitproj, numgitprojs, numscraped)"""
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

