import pdb
import json
from bs4 import BeautifulSoup
import urllib2
import re
import sys
import urllib
import json
import time


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
    
class Repository:
    def query(self, entry, pagenumber = 0): return ""
    def parse(self, raw): return {}
    def build(self, result): return {}
    def getPubsCount(self, entry):
        refs = []
        try:
            pp = 0
            while True:
                #throttle
                time.sleep(2)             
    
                qry = self.query(entry,pp)
                raw = urllib2.urlopen(qry).read()
    
                thedata = self.parse(raw)
                for result in thedata:
                    try:
                        ref = self.build(result)
                        refs.append(ref)
                    except Exception as e:
                        print "Error: ", self.__class__.__name__, e
    
                if (len(thedata) < 100):
                    break
    
                pp = pp + 1
            
        except Exception as e:
            print "Error:", self.__class__.__name__, repr(e)
            citationCount = 0
            citationLink = ""
        return refs

#
# Look up entry in PLOS
#
class Plos(Repository):
    def query(self, entry, pagenumber = 0):
        plosApiKey = "haGw_qJ4q8HLcYERQK8x"
    
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
    

    
        return ("http://api.plos.org/search?q=" +
                  urllib.quote(thequery) +
                  "&api_key=" + plosApiKey +
                  "&rows=100&wt=json&start="+str(pagenumber*100))


    def parse(self, raw): return json.loads(raw)["response"]["docs"]
    def build(self, result): 
        return { "url": "http://dx.doi.org/" + result["id"],
            "year": result["publication_date"][:4],
            "title":   result["title_display"] + "(" + result["article_type"] + ")",
            "abstract": "",
            "repository": "plos",
            "volume":   "",
            "authors": result["author_display"],
            "journal": result["journal"],
            "pages": "",
            "location": ""}
    
#
# Look up entry in PMC europe
#
class Ebi(Repository):

    def query(self, entry, pagenumber = 0):
    
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
    
        return "http://www.ebi.ac.uk/europepmc/webservices/rest/search/query=" + urllib.quote(thequery, "():/") + "&dataset=fulltext&page=" + str(pagenumber+1) + "&resultType=core&format=json"
    
    
    def parse(self, raw): return json.loads(raw)['resultList']['result']


    def build(self, result):
       record = { 
            "year": result["journalInfo"].get("yearOfPublication","??"),
            "title":   result["title"],
            "repository": "ebi",
            "volume":   result["journalInfo"].get("volume",""),
            "issue":   result["journalInfo"].get("issue",""),
            "authors": result["authorString"],
            "abstract": "",
            "journal": result["journalInfo"]["journal"]["title"],
            "pages": result.get("pageInfo", ""),
            "location": ""}
       if ("doi" in result):
            record["url"] = "http://dx.doi.org/" + result["doi"]
       return record


    
if __name__ == "__main__":
    appf = open("../../../data/appinfo.R.json", "r")
    apps = json.loads(appf.read())
    entry = apps[sys.argv[1]]
    plosrefs = Plos().getPubsCount(entry)
    ebirefs = Ebi().getPubsCount(entry)
    print "Found ", len(plosrefs), " PLOS refs and ", len(ebirefs), " EBI refs"


