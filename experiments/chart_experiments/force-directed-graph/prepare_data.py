#!/usr/bin/python

import json
import sys
import math

counter = 0
threshold = 10
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
		co, self = fields[0], fields[2]
		print self
		if co > threshold:
			for i in range(3, len(fields)-1):
				app,value = fields[i].split(":")
				if app == self:
						continue
				links.append({
					"source": new_app(self),
					"target": new_app(app),
					"value" : int(math.log(float(value)))})
		if len(links) > threshold*threshold:
				break
nodes = []
for a in apps:
	nodes.append({"name":a, "group":1})
with open('links.json', 'w') as outfile:
		json.dump({"links":links, "nodes": nodes}, outfile)
