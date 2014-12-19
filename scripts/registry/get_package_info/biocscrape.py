from bs4 import BeautifulSoup
from urllib2 import urlopen
import json
import re
import time
import pdb
import bibtexparser  # pip install bibtexparser

packagelist = "http://master.bioconductor.org/packages/json/3.0/bioc/packages.js"

def biocCiteUrl(pkg): return "http://master.bioconductor.org/packages/release/bioc/citations/" + pkg + "/citation.html"

packageJs = urlopen(packagelist).read()
packageJs = packageJs.replace("var bioc_packages = ","")[0:-1]
bioclist = json.loads(packageJs)
bioc = dict()

count = 1
for entry in bioclist["content"]:
    print count, "of", len(bioclist["content"]), ": ", entry[0]
    count += 1
    if entry[0] in bioc:
        print "OVERLAP ",entry[0]
    else:
        bioc[entry[0]] = { 
          "match" : [entry[0]],
          "title" : entry[0],
          "cite_author" : entry[1],
          "cite_title" : entry[2],
          "raw_cite" : entry[2] + " " + entry[0],
          "image": "unknown.png",
          "short_description": entry[2],
          "version": "all",
          "publications": 0,
          "website" : "http://www.bioconductor.org/packages/release/bioc/html/" + entry[0] + ".html",
          "description" : entry[2] 
       }
    try:
        time.sleep(1)
        bioc[entry[0]]["raw_cite"] = BeautifulSoup(urlopen(biocCiteUrl(entry[0])).read()).get_text().replace("\n"," ")
    except:
        print "Citation not found"


with open("bioc3.json", "w") as f:
    f.write(json.dumps(bioc, indent=3))

