import json
from bs4 import BeautifulSoup
import urllib2
import urllib
import time

cranf = open("craninfo3.json", "r")
biocf = open("bioc3.json", "r")

cran = json.loads(cranf.read())
bioc = json.loads(biocf.read())

for entry in cran:
    cran[entry]["repository"] = "cran"

for entry in bioc:
    if entry in cran:
        print "OVERLAP ",bioc[entry]["title"]
    else:
        cran[entry] = bioc[entry]
        cran[entry]["repository"] = "bioconductor"

outf = open("appinfo.R.json", "w")
outf.write( json.dumps(cran, indent=4))
outf.close()

