
import pdb
import json
from bs4 import BeautifulSoup
import urllib2
import re
import sys
import urllib
import json
import time

plosApiKey = "haGw_qJ4q8HLcYERQK8x"

appf = open("appinfo.R.json", "r")
#cranf = open("craninfo3.json", "r")
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


# TEST:
aln = authorsLastnames("Gaston Sanchez [aut, cre],\nLaura Trinchera [aut],\nGiorgio Russolillo [aut]")
assert set(aln) == set(["Sanchez", "Trinchera", "Russolillo"]), "authorsLastnames: " + str(aln)
    
# Look up entry in PLOS
#
def plos(entry, pagenumber = 0):
    # Throttle
    time.sleep(2)

    auths = authorsLastnames(entry["cite_author"])

    if (entry.get("repository", "cran") == "cran"):
        urls=("http://cran.r-project.org/package*" + entry["title"] +
                    "\" OR everything:\"" +
                    entry["website"].replace("/index.html",""))
    elif (entry.get("repository", "cran") == "bioconductor"):
        urls=entry["website"]

    doiquery = '';
    if ("dx.doi.org" in entry.get("raw_cite","")):
        doi = re.search("doi.org/(10[^, \n\t\"\']*)", entry["raw_cite"])
        if doi:
           doiquery = ' OR (reference: "{doi}")'.format(doi=doi.group(1))

    thequery = ("(everything: \"{title}\") " +
           "OR (reference: \"{namedesc}\") " +
           doiquery +
           "OR (everything: \"{urls}\")").format(
                title=entry["title"].strip() +
                   ": " + entry["short_description"].strip(),
                namedesc= "\" AND \"".join(auths + [entry["title"].strip(), 
                                           entry["short_description"].strip()]),
                urls=urls
    )


    print thequery

    return ("http://api.plos.org/search?q=" +
              urllib.quote(thequery) +
              "&api_key=" + plosApiKey +
              "&rows=100&wt=json&start="+str(pagenumber*100))
    

def getPubsCount(packageTitle):
    entry = apps[packageTitle]
    refs = []
    pdb.set_trace()
    try:
        pp = 0
        while True:
            qry = plos(entry,pp)
            print "Querying ", qry
            raw = urllib2.urlopen(plos(entry,pp)).read()

            plosdata = json.loads(raw)["response"]["docs"]
            for result in plosdata:
                result["abstract"] = ""
                ref = { "url": "http://dx.doi.org/" + result["id"],
                        "year": result["publication_date"][:4],
                        "title":   result["title_display"] + "(" + result["article_type"] + ")",
                        "volume":   "",
                        "authors": result["author_display"],
                        "journal": result["journal"],
                        "pages": "",
                        "location": ""}
                refs.append(ref)

            if (len(plosdata) < 100):
                break

            pp = pp + 1
        
    except Exception as e:
        print packageTitle, "Error:", str(e)
        citationCount = 0
        citationLink = ""
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(refs)
    
if __name__ == "__main__":
    getPubsCount(sys.argv[1])

