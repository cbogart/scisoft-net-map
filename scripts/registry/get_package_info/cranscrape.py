from bs4 import BeautifulSoup
from urllib2 import urlopen
import json
import re
import pdb
import bibtexparser  # pip install bibtexparser

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
            "searchstring": name,
            "version": "all",
            "publications": 0,
            "website" : site,
            "description" : desc }
        try:
            detailsoup = BeautifulSoup(urlopen(site).read(), "lxml")
            author = detailsoup.find('td', text = 'Author:').findNext("td").text 
            maintainer = detailsoup.find('td', text = 'Maintainer:').findNext("td").text 
            try:
               citationsite = detailsoup.find('td', text = 'Citation:').findNext("td").a["href"] 
               citationsite = site.replace("index.html", citationsite)
               citetext = urlopen(citationsite).read()
               bib = bibtexparser.loads(citetext)
               titles = bib.entries[0]["title"].replace("}","").replace("{","").replace("\n","")
               authors = bib.entries[0]["author"].replace("}","").replace("{","").replace("\n","")
               searchstring  = titles + " " + authors
            except Exception, e:
               searchstring = author + " " + name
            pack[name]["searchstring"] = searchstring
        except Exception, e:
            print "ERROR:", e
   

print json.dumps(pack, indent=3)

