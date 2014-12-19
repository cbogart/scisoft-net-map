import json
from bs4 import BeautifulSoup
import urllib2
import sys
import urllib
import pdb
import time
import re

userAgent = """Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36"""
opener = urllib2.build_opener()
opener.addheaders = [('User-agent', userAgent)]

def authorsLastnames(authstring):
    auths = [au.strip().split()[-1] for au in re.sub(r'\[.*?\]',"",authstring).split(",")]
    return auths

def stripParens(s):
    return re.sub(r'\(.*?\)',"",s)

def stripRVersion(s):
    return re.sub(r'R package version.*','',s)

def get_searchstring(entry):
    if entry["repository"] == "cran":
        searchstring = " ".join(authorsLastnames(entry["cite_author"])) + " " + entry["cite_title"]
    elif entry["repository"] == "bioc":
        if ("raw_cite" in entry): 
            searchstring=stripParens(stripRVersion(entry["raw_cite"]))
        else:
            searchstring = " ".join(authorsLastnames(entry["cite_author"])) + " " + entry["cite_title"]
    else:
        return ""

    # Get rid of non-ascii gobbledygook
    nonweird = str(re.sub(r'[^\x00-\x7F]+',' ', searchstring))

    # Throw away page numbers
    nonweird = re.sub(r'pp\. \d+\w?-\d+', ' ', nonweird)

    # If there's a DOI, return that alone; GScholar knows about dois
    dois = re.search(r'(doi.org/[^,; ]+)', nonweird) 
    if (dois and dois.groups()):
       return "http://dx." + dois.groups()[0]

    # Otherwise, strip out any http: junk embedded in the citation
    else:
       return re.sub(r'http://[^ ]+', "", nonweird)

def unquote(x):
    if (x.startswith('"') and x.endswith('"')):
        return x[1:-1]
    else:
        return x
        
def googleScholar(ref):
    time.sleep(5)
    return "http://scholar.google.com/scholar?q=" + urllib.quote(ref)
    
def getPubsCount(entry):
    try:
        pdb.set_trace()
        searchstring = get_searchstring(entry)
        raw = opener.open(googleScholar(searchstring)).read()
        theGoogle = BeautifulSoup(raw)
        
        sec = theGoogle.find("div", class_="gs_ri") 
        foundTitle = sec.find(class_="gs_rt").get_text() 
        citations = sec.find("a", text=re.compile("Cited by.*"))
        
        if (citations.get_text().startswith("Cited by")):
            citationCount = int(citations.get_text()[9:])
            citationLink = "http://scholar.google.com" + citations.attrs["href"]
        else:
            citationCount = 0
            citationLink = ""
        return (citationCount, citationLink)
        
    except Exception as e:
        print raw
        print "ERR", entry["title"], searchstring, e, repr(sec)
        citationCount = 0
        citationLink = ""
        return (citationCount, citationLink)
    
if __name__ == "__main__":
    getPubsCount(sys.argv[1])

