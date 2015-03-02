import sqlite3
import json

class RepoScrape:
    def __init__(self, dbname):
        self.db = sqlite3.getConnection(dbname)

    def makeAppInfo(self, appinfoFileName):
       """Dump info from database into appinfo.R.json"""
       packages = self.db.execute("select * from packages")      

        # prefer cran to bioc to github
       appinfo = {}

       oldappinfo = json.loads(
          open("../../data/appinfo.R.handedited.json", "r").read())

       for pack in packages:
           name = pack["name"]
           appinfo[name] = oldappinfo[name]
           appinfo[name]["website"]= pack[name]["url"],
           appinfo[name]["description"]= pack[name]["description"],
           appinfo[name]["title"]= pack[name]["title"],
           appinfo[name]["short_description"]=pack[name]["title"],
           appinfo[name]["match"]=[ name ]
           }

       with open(appinfoFileName, "w") as f: 
           f.write(json.dumps(appinfo, indent=4))


    def getGitDailyImportCount(self):
       """package -> day -> number"""
       return { "pkgA" : { "2015-01-01": 14 } }

    def getGitCoOccurrence(self):
       """package->package->number"""
       return { "pkgA": { "pkgB": 14 } }

    def getGitCounts(self):
       """(lastgitproj, numgitprojs, numscraped)"""
       return (0,0,0)


