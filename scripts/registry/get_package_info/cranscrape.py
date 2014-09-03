from bs4 import BeautifulSoup
from urllib2 import urlopen
import json

directory = "http://cran.r-project.org/web/packages/available_packages_by_date.html"

html = urlopen(directory).read()
soup = BeautifulSoup(html, "lxml")
tablerows = soup.findAll("tr")
pack = dict()
for row in tablerows:
    cols = row.findAll("td")
    if len(cols) == 3:
        name = cols[1].a.string
        site = "http://cran.r-project.org" + cols[1].a["href"][5:]
        desc = cols[2].string
        pack[name] = { 
            "match" : [name],
            "title" : name,
            "image": "unknown.png",
            "short_description": desc,
            "version": "all",
            "publications": 0,
            "website" : site,
            "description" : desc }
   

print json.dumps(pack, indent=3)

