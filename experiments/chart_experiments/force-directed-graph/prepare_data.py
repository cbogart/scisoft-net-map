#!/usr/bin/python

import json
import sys
import math

counter = 0
limit = 75 
lo, hi = 10, 20 
links = []
apps = {}

def new_app(hash):
		global counter
		if hash not in apps:
			apps[hash] = counter
			counter+=1
		return apps[hash]


with open(sys.argv[1]) as f:
	for line in f.readlines():
		fields = line.split(";")
		co, self = int(fields[0]), fields[2]
		if lo < co  < hi:
			print self, len(apps)
			for i in range(3, min(len(fields)-1, 500)):
				app,value = fields[i].split(":")
				if app == self:
						continue
				links.append({
					"source": new_app(self),
					"target": new_app(app),
					"value" : int(math.log(float(value)))})
		if counter > limit:
			break
print counter
nodes = []
for a in apps:
	nodes.append({"name":a, "group":1})
with open('links.json', 'w') as outfile:
		json.dump({"links":links, "nodes": nodes}, outfile)
