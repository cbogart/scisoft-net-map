#!/usr/bin/python

import json, sys, os 
import datetime
import collections
from os import walk

class App:
	def __init__(self, hash):
		self.hash = hash
		self.coapps= collections.defaultdict(int)
		self.total = 0

	def appendApps(self, app_list):
		for hash in app_list:
			self.coapps[hash] += 1
		self.total += len(app_list)

	def __repr__(self):
		return "{} \n".format(self.runs, self.name)

def process_file(filename, apps):
	f = open(filename)
	j = json.load(f)
	l,cnt = len(j),0	
	for session_key, session  in j.iteritems():
		cnt+=1
		session_apps = []
		if len(session) < 2:
			continue
		sys.stdout.write("[%d%%]" % (int(cnt*100/l)))
		for run in session:
			hash = run["sha1"]
			if hash in apps:
				a = apps[hash]
			else:
				apps[hash] = App(hash)
			session_apps.append(hash)
		for app_hash in session_apps:
			apps[app_hash].appendApps(session_apps)
		sys.stdout.write("\r")
		sys.stdout.flush()
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
		coapps = apps[key].coapps
		f.write("{};{};{}".format(len(coapps), apps[key].total, key))
		for app in coapps:
			f.write(";{}:{}".format(app,coapps[app]))
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
	#	try:
		process_file(f, apps)
		print "[{}%]\t{} is ready".format(int(progress*100/l), os.path.basename(f))
	#	except:
	#		print "error on file: " + f 
	writeResults(apps)	

if __name__ == '__main__':
	main()
