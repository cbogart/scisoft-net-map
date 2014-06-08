#!/usr/bin/python

import json
import sys
import math

counter = 0
limit =25 
lo, hi = 10, 100 
links = []
apps = {} 

def new_app(hash):
		global counter
		if hash not in apps:
			apps[hash] = counter
			counter+=1
		return apps[hash] 
# setup links
for i in range(limit):
	links.append([0] * limit)

with open(sys.argv[1]) as f:
	for line in f.readlines():
		fields = line.split(";")
		co, self = int(fields[0]), fields[2]
		if lo < co  < hi:
			print self, len(apps)
			for i in range(3, min(len(fields)-1, 500)):
				app, value = fields[i].split(":")
				if counter > limit - 3: break
				i, j = new_app(self), new_app(app)
				links[i][j] += int(value)
				links[j][i] = links[i][j]
		if counter > limit:
			break
print counter
apps_reversed = {v:k for k, v in apps.items()}
for i in range(limit):
	sys.stdout.write("\n")
	for j in range(limit):
		sys.stdout.write('%d\t' % (links[i][j]) )
