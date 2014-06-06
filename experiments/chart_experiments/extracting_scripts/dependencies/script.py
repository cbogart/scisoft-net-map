#!/usr/bin/python

import json, sys, os 
import datetime
import collections
from os import walk
from itertools import islice

def window(seq, n=2):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result    
    for elem in it:
        result = result[1:] + (elem,)
        yield result

class App:
	def __init__(self, hash, id):
		self.id = id
		self.hash = hash
		self.followers = collections.defaultdict(int)
		self.total = 0

	def followed_by(self, app):
		hash = app.hash
		self.followers[hash] += 1
		self.total += 1

	def __repr__(self):
		return "{} \n".format(self.runs, self.name)
def get_app(hash, apps):
	if hash not in apps:
		apps[hash] = App(hash, len(apps))
	return apps[hash]

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
		for (run1, run2) in window(session):
			hash1 = run1["sha1"]
			hash2 = run2["sha1"]
			app1 = get_app(hash1, apps)
			app2 = get_app(hash2, apps)
			app1.followed_by(app2)
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
	l = len(apps)
	progress = 0
	for key in apps:
		sys.stdout.write("\r[{} out of {}]".format(progress, l))
		sys.stdout.flush()
		progress += 1
		followers = apps[key].followers
		total = apps[key].total
		f.write("{};{};".format(len(followers), apps[key].id))
		for key2 in apps:
			if key2 in followers:
				num = followers[key2]
			else:
				num = 0
			f.write("{}:{};".format(apps[key2].id, num))
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
		try:
			process_file(f, apps)
			print "[{}%]  {} is ready".format(int(progress*100/l), os.path.basename(f))
		except:
			print "error on file: " + f 
	writeResults(apps)	

if __name__ == '__main__':
	main()
