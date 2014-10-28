
import json
from bs4 import BeautifulSoup
import urllib2
import sys
import urllib
import time

#
#  This program does not work.
#  Google scholar blocks programmatic queries
#  Bah.
#

cranf = open("craninfo2.json", "r")
#bioc = open("bioc2.json", "r")

cran = json.loads(cranf.read())

def unquote(x):
    if (x.startswith('"') and x.endswith('"')):
        return x[1:-1]
    else:
        return x
        
def googleScholar(ref):
    time.sleep(10)
    return "http://scholar.google.com/scholar?q=" + urllib.quote(ref)
    
def getPubsCount(packageTitle):
    entry = cran[packageTitle]
    try:
        theGoogle = BeautifulSoup(urllib2.urlopen(googleScholar(entry["searchstring"])).read())
        
        sec = theGoogle.find("div", class_="gs_ri") 
        foundTitle = sec.find("div", class_="gs_rt").a.get_text() 
        foundInfo = sec.find("div", class_="gs_a").get_text() 
        citations = sec.find("div", class_="gs_gl").find('a')
        pdb.set_trace()
        
        if (a.get_text().startswith("Cited by")):
            citationCount = int(a.get_text()[9:])
            citationLink = a.href
        else:
            citationCount = 0
            citationLink = ""
        print c, citationCount, "citations", citationLink
        
    except Exception as e:
        print packageTitle, "Error:", str(e)
        citationCount = 0
        citationLink = ""
    
if __name__ == "__main__":
    getPubsCount(sys.argv[1])

