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

assert calcDependencyClosure(["a", "b", "c"], { "a" : ["b", "d"], "c" : ["a"] })== {"a": ["b", "d"], "b": [], "c": ["a"] }, \
        calcDependencyClosure(["a", "b", "c"], { "a" : ["b", "d"], "c" : ["a"] })

def wayupstream(package1, package2, closedDepList, skipFirstLevel=True, cycleCheck = 0):
    """Semantics: Is package1 wayupstream of package2, i.e. does package 2 require stuff that requires package1?
    Should IGNORE whether package1 is a direct parent of package2; we're ONLY looking for distant ancestry"""
    if cycleCheck > len(closedDepList.keys()):
        raise Exception("Dependency list is circular around " + package1 + " and " + package2)
    #pdb.set_trace()
    for parent in closedDepList.get(package2,[]):
        if package1 == parent and skipFirstLevel==False: return True
        if wayupstream(package1, parent, closedDepList, skipFirstLevel=False, cycleCheck = cycleCheck + 1): return True
    return False

def waydownstream(package1, package2, closedDepList):
    return wayupstream(package2, package1, closedDepList)

assert wayupstream("a", "b", { "b": ["a"], "a": [] }) == False
assert wayupstream("a", "c", { "b": ["a"], "c": ["b"], "a": [] }) == True
assert wayupstream("c", "a", { "b": ["a"], "c": ["b"], "a": [] }) == False

ancestor_cache = dict()
def all_ancestors(package, deps, depth=0):
    if package in ancestor_cache: return ancestor_cache[package]
    if depth == 0:
        print "finding ancestors of", package
    if package == "R": return []
    if depth > 200:
        ancestor_cache[package] = []
        return []
        #raise Exception("depth of recursion error on package " + package + " deps are " + str(deps[package]))
    anc = set([])
    for parent in set(deps.get(package,[])):
        #print package, "lvl", depth, "checking", parent
        if parent != package:            
            anc.add(parent)
            anc = anc.union(all_ancestors(parent, deps, depth=depth+1))
    ancestor_cache[package] = anc
    return anc

def all_paths(deps):
    global ancestor_cache 
    ancestor_cache = dict()
    return { k : all_ancestors(k,deps) for k in deps }

def canonicalize_dep_tree(deps):
    #print "building closure"
    paths = all_paths(deps)
    #print "reducing excess links"
    for down in deps:
        #print down
        dontneed = set([])
        for up in deps[down]:
            for otherup in deps.get(down,[]):
                if otherup != up:
                    if up in paths.get(otherup,[]):
                        dontneed.add(up)
                        break
        deps[down] = list(set(deps[down])-dontneed)
    return deps
                    

deptest = { "a": ["b","c","d"], "b": ["c"], "c": [], "d": [] }
deptest = canonicalize_dep_tree(deptest)
assert deptest["a"] == ["b","d"], "Deptest = " + str(deptest)
assert deptest["b"] == ["c"]
assert deptest["c"] == []

def getConnection(dbname):
    # Open the database
    conn = sqlite3.connect(dbname)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma short_column_names=OFF;");
    conn.execute("pragma full_column_names=ON;");
    return conn

def iso2epoch(dt):
    return datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S").strftime("%s")

# NB: R packages must start with letter; must not end with period, and must
# contain only letters, numbers, and periods.  
legalimport = re.compile("^[a-zA-Z][a-zA-Z0-9\.]*[a-zA-Z0-9]$")
    
    
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
        uses = self.db.execute("""
            select gitprojects.*, group_concat(distinct(package_name)) deps, count(distinct(gitfiles.path)) descfiles from gitprojects 
            left join gitimports on gitprojects.id=gitimports.project_id 
            left join gitfiles on gitprojects.id=gitfiles.project_id and path like "%DESCRIPTION"
            where gitprojects.cb_last_scan > 0 
                   and gitprojects.error = '' and gitprojects.deleted = '0'
            group by gitprojects.id having deps!='';
            """);
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
               "is_package": use["descfiles"],
               "is_fork": 1 if use["gitprojects.forked_from"] != "" else 0,
               "cb_last_scan": use["gitprojects.cb_last_scan"],
               "pushed_at": use["gitprojects.pushed_at"],
               "watchers_count": use["gitprojects.watchers_count"],
               "stargazers_count": use["gitprojects.stargazers_count"],
               "forks_count": use["gitprojects.forks_count"],
               "dependencies": deps  #filter(legalimport.match, use["deps"].split(","))
            }
            referers.append(ref)
        return referers

    def makeAppInfo(self, includeHandEditedAppInfo=False):
       """Dump info from database into appinfo.R.json"""
       packages = self.db.execute("""
           select packages.*, group_concat(distinct(tags.tag)) views from packages 
           left join tags on packages.name = tags.package_name group by packages.name;
       """)

        # prefer cran to bioc to github
       self.appinfo = {}
       self.deps = {}

       if includeHandEditedAppInfo:
           oldappinfo = json.loads(
                open("../../data/appinfo.R.handedited.json", "r").read())
       else:
           oldappinfo = {}
           
       for pack in packages:
           name = pack["packages.name"]
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
           self.deps[dep["staticdeps.package_name"]].append(dep["staticdeps.depends_on"])
           
       canonicalize_dep_tree(self.deps)

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
       allcounts = defaultdict(lambda: defaultdict(int))
       directcounts = defaultdict(lambda: defaultdict(int))
       for r in refs:
           deps = filter(legalimport.match, (r["deps"] or "").split(","))
           alldeps = calcDependencyClosure(deps, self.deps)
           upstreams = [d for i in alldeps for d in alldeps[i]]
           #if "Biobase" in deps and "Biostrings" in deps:
               #print r
               #pdb.set_trace()
           
           # logical_codeps = things they explicitly included, but excluding anything they 
           #   didn't really have to include (because R would have inferred it as a dependency)
           logical_codeps = set(deps) - set(upstreams)   
           alldepscomplete = set(alldeps.keys() + upstreams)
           for d1 in alldepscomplete:
               allcounts[d1][r["lastcommit"]] += 1
               if d1 in alldeps:
                   directcounts[d1][r["lastcommit"]] += 1
               for d2 in alldepscomplete:
                   if (d1 != d2):
                       if d2 in alldeps.get(d1, []):   linktype = "upstream"
                       elif d1 in alldeps.get(d2, []): linktype = "downstream"
                       #elif d1 in logical_codeps and d2 in logical_codeps: linktype = "usedwith"
                       #else: linktype="ancestry"
                       elif d1 in deps and d2 in deps: linktype="usedwith"
                       else: linktype = "ancestry"
                       if "Biobase" in deps and "Biostrings" in deps:
                           print d1, d2, linktype
                       if linktype != "ancestry":
                           cocounts[d1][d2] = (linktype, cocounts[d1][d2][1]+1)
       return (allcounts, directcounts, cocounts)

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

