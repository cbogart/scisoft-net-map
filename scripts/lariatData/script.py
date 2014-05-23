#!/usr/bin/python

import json, sys, os 
import datetime
import collections
from os import walk

class App:
	def __init__(self, hash):
		self.hash = hash
		self.runs = collections.defaultdict(int)
		self.total = 0

	def addRun(self, run, session_key):
		dt = datetime.datetime.fromtimestamp(float(run["startEpoch"]))
		date = dt.date().__str__()
		self.runs[date] += 1
		self.total += 1
		self.name = run["exec"]

	def __repr__(self):
		return "{} \n".format(self.runs, self.name)

def process_file(filename, apps):
	f = open(filename)
	j = json.load(f)
	
	for session_key, session  in j.iteritems():
		for run in session:
			hash = run["sha1"]
			name = run["exec"]
			a = None
			if hash in apps:
				a = apps[hash]
			else:
				apps[hash] = App(hash)
				a = apps[hash]
			a.addRun(run, session_key)
	f.close()

def get_list_of_files(path):
	files = []
	for (root, dirnames, filenames) in walk(path):
		for filename in filenames:
			files.append(os.path.join(root, filename))
		break
	return files

def writeResults(apps):
	f = open("output.tsv", 'w')
	for key in apps:
		f.write("{};{}".format(apps[key].total, key))
		runs = apps[key].runs
		for dt in sorted(runs):
			f.write(";{}:{}".format(dt,runs[dt]))
		f.write("\n")
	f.close()
	
def main():
	if len(sys.argv) < 2:
		print "usage: {} AHHA_MSIT-project2014_Root/\[General\]\ From\ Client/data\ for\ MSI\ team/lariatData".format(sys.argv[0])
		return
	apps = dict()
	files = get_list_of_files(sys.argv[1])
	progress = 0
	l = len(files)
	for f in get_list_of_files(sys.argv[1]):
		progress += 1
		print "[{}%]\tprocessing {}".format(int(progress*100/l), os.path.basename(f))
		try:
			process_file(f, apps)
		except:
			print "error on file: " + f 
	writeResults(apps)	

if __name__ == '__main__':
	main()
