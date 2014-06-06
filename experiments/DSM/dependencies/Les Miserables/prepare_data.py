#!/usr/bin/python

import json
import sys
import math

counter = 0
limit =  50
lo, hi = 10 , 150
links = []
apps = {}


print "Filtering apps first"
with open(sys.argv[1]) as f:
	counter = 0
	for line in f.readlines():
		counter += 1
		sys.stdout.write("\r%d: %d / %d" % (counter, len(apps), limit))
		fields = line.split(";")
		total, self = int(fields[0]), fields[1]
		if lo < total  < hi:
			apps[self] = len(apps)
		for i in range(2, len(fields)-1):
			app, value = fields[i].split(":")
			val = int(value)
			if app == self: continue
			if val > 20:
				apps[app] = len(apps)
		if len(apps) > limit:
			break
	print "..done"
print "Collecting links..."
with open(sys.argv[1]) as f:
	counter = 0
	for line in f.readlines():
		counter += 1
		sys.stdout.write("\r%d" % counter)
		fields = line.split(";")
		total, self = int(fields[0]), fields[1]
		if self not in apps: continue
		for i in range(2, len(fields)-1):
			app, value = fields[i].split(":")
			if app not in apps: continue
			if app == self: continue
			val = int(value)
			links.append({
				"source": int(apps[self]),
				"target": int(apps[app]),
				"value" : int(math.log(val)) if val > 1 else 0})
	print "...done"
nodes = []
print "writing results"
for a in apps:
	nodes.append({"name":a, "group":1})
with open('links.json', 'w') as outfile:
		json.dump({"links":links, "nodes": nodes}, outfile)
