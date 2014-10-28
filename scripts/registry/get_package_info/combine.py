
import json
from bs4 import BeautifulSoup
import urllib2
import urllib
import time

cranf = open("craninfo.json", "r")
biocf = open("bioc.json", "r")

cran = json.loads(cranf.read())
bioc = json.loads(biocf.read())

for entry in bioc["content"]:
    if entry[0] in cran:
        print "OVERLAP ",entry[0]
    else:
        cran[entry[0]] = { 
          "match" : [entry[0]],
          "title" : entry[0],
          "image": "unknown.png",
          "short_description": entry[2],
          "version": "all",
          "publications": 0,
          "website" : "http://www.bioconductor.org/packages/release/bioc/html/" + entry[0] + ".html",
          "description" : entry[2] 
       }
       
def unquote(x):
    if (x.startswith('"') and x.endswith('"')):
        return x[1:-1]
    else:
        return x
        
def googleScholar(ref):
    time.sleep(10)
    return "http://scholar.google.com/scholar?q=" + urllib.quote(ref)
    
for c in cran:
    entry = cran[c]
    if "cran.r-project" in entry["website"]: 
        citesite = "http://cran.r-project.org/web/packages/" + c + "/citation.html"
        extractAll = lambda soup: unquote(soup.find('blockquote').p.get_text())
    elif "bioconductor" in entry["website"]:
        citesite = entry["website"].replace(".html","").replace("/html/","/citations/") + "/citation.html"
        #extractAll = lambda soup: unquote(soup.find("div", class_="bioc_citation").p.get_text())
        extractAll = lambda soup: soup.get_text().replace(" (????)","")
    time.sleep(1)
    try:
        content = BeautifulSoup(urllib2.urlopen(citesite).read())
        import pdb
        pdb.set_trace()
        pubsrch = extractAll(content)
        
        theGoogle = BeautifulSoup(urllib2.urlopen(googleScholar(pubsrch)).read())
        
        sec = theGoogle.find("div", class_="gs_ri") 
        foundTitle = sec.find("div", class_="gs_rt").a.get_text() 
        foundInfo = sec.find("div", class_="gs_a").get_text() 
        citations = sec.find("div", class_="gs_gl").find('a')
        
        if (a.get_text().startswith("Cited by")):
            citationCount = int(a.get_text()[9:])
            citationLink = a.href
        else:
            citationCount = 0
            citationLink = ""
        print c, citationCount, "citations"
    except Exception as e:
        print c, "Error:", str(e)
        citationCount = 0
        citationLink = ""
        
    entry["publications"] = citationCount
    entry["publicationsUrl"] = citationLink
    
print json.dumps(cran, indent=4)

outf = open("appinfo.R.json", "w")
outf.write( json.dumps(cran, indent=4))
outf.close()

