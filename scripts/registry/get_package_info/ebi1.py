import pdb
import json
from bs4 import BeautifulSoup
import urllib2
import re
import sys
import urllib
import json
import time

import pprint
prettyprinter = pprint.PrettyPrinter(indent=4)

appf = open("appinfo.R.json", "r")
#bioc = open("bioc2.json", "r")

apps = json.loads(appf.read())

def unquote(x):
    if (x.startswith('"') and x.endswith('"')):
        return x[1:-1]
    else:
        return x

def authorsLastnames(authstring):
    authstring = re.sub(r'<.*?>',"",authstring)
    authstring = re.sub(r'\[.*?\]',"",authstring)
    auths = [au.strip().split()[-1] for au in authstring.split(",")]
    return auths

aln = authorsLastnames("Gaston Sanchez [aut, cre],\nLaura Trinchera [aut],\nGiorgio Russolillo [aut]")
assert set(aln) == set(["Sanchez", "Trinchera", "Russolillo"]), "authorsLastnames: " + str(aln)
    
def ebi(entry, pagenumber = 0):
    time.sleep(2)

    auths = authorsLastnames(entry["cite_author"])
    doiquery = ""
    if ("dx.doi.org" in entry.get("raw_cite","")):
        doi = re.search("doi.org/(10[^, \n\t\"\']*)", entry["raw_cite"])
        if doi:
           doiquery = ' OR (REF:{doi})'.format(doi=doi.group(1))

    thequery = "((REF:\"{title}\") AND {authors}) {doiquery} OR ({urls})".format(
        doiquery=doiquery,
        title=entry["title"].strip() + ": " + entry["short_description"].strip(),
        authors=" AND ".join(['(REF:"' + a + '")' for a in auths]),
        urls='(BODY:"http://cran.r-project.org/package*' + entry["title"] + '") OR (BODY:"' + entry["website"].replace("/index.html","") + '")'
    )
    #thequery = thequery.replace("/","*")
    thequery = thequery.replace("=","*")

    print thequery
    return "http://www.ebi.ac.uk/europepmc/webservices/rest/search/query=" + urllib.quote(thequery, "():/") + "&dataset=fulltext&page=" + str(pagenumber+1) + "&resultType=core&format=json"
    

def getPubsCount(packageTitle):
    entry = apps[packageTitle]
    refs = []
    try:
        while True:
            pp = 0
            qry = ebi(entry,pp)
            print "Querying ", qry
            raw = urllib2.urlopen(ebi(entry,pp)).read()

            print "-------------"
            print raw
            print "-------------"
            ebidata = json.loads(raw)['resultList']['result']
            prettyprinter.pprint(ebidata)
            print "============="
            for result in ebidata:
                result["abstract"] = ""
                ref = { "url": "http://dx.doi.org/" + result["doi"],
                        "year": result["journalInfo"].get("yearOfPublication","??"),
                        "title":   result["title"],
                        "volume":   result["journalInfo"].get("volume",""),
                        "issue":   result["journalInfo"].get("issue",""),
                        "authors": result["authorString"],
                        "journal": result["journalInfo"]["journal"]["title"],
                        "pages": result.get("pageInfo", ""),
                        "location": ""}
                refs.append(ref)

            if (len(ebidata) < 100):
                break

            pp = pp + 1
        
    except Exception as e:
        print packageTitle, "Error:", str(e)
        citationCount = 0
        citationLink = ""
    prettyprinter.pprint(refs)
    
if __name__ == "__main__":
    getPubsCount(sys.argv[1])

