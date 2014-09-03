
import json

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

print json.dumps(cran, indent=4)
   

