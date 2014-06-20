#!/usr/bin/python

import json, sys, os 
import datetime
import collections
from os import walk

class App:
	def __init__(self, hash ):
		self.hash = hash
		self.daily= collections.defaultdict(int)
		self.weekly = collections.defaultdict(int)
		self.monthly= collections.defaultdict(int)

	def addRun(self, run):
		dt = datetime.datetime.fromtimestamp(float(run["startEpoch"]))
		day = dt.date().__str__()
		self.daily[day] += 1

		iso = dt.isocalendar()
		week = "{}-{}".format(iso[0], iso[1])
		self.weekly[week] += 1

		month = "{}-{}".format(iso[0], dt.month)
		self.monthly[month] += 1

def process_file(filename, app, app_hash):
	f = open(filename)
	j = json.load(f)
	
	for session_key, session  in j.iteritems():
		for run in session:
			hash = run["sha1"]
			if app_hash != hash:
				continue
			app.addRun(run)
	f.close()

def get_list_of_files(path):
	files = []
	for (root, dirnames, filenames) in walk(path):
		for filename in filenames:
			files.append(os.path.join(root, filename))
		break
	return files

def writeResults(app):
	for prop in ['daily', 'weekly', 'monthly']:
		f = open("{}-{}.tsv".format(app.hash, prop), 'w')
		data = getattr(app,prop)
		for dt in sorted(data):
			f.write("{}:{}\n".format(dt,data[dt]))
		f.close()
	
def main():
	if len(sys.argv) < 3:
		print "usage: {} AHHA_MSIT-project2014_Root/\[General\]\ From\ Client/data\ for\ MSI\ team/lariatData APPHASH".format(sys.argv[0])
		return
	files = get_list_of_files(sys.argv[1])
	app_hash = sys.argv[2]
	app = App(app_hash)
	progress = 0
	l = len(files)
	for f in get_list_of_files(sys.argv[1]):
		progress += 1
		print "[{}%]\tprocessing {}".format(int(progress*100/l), os.path.basename(f))
		process_file(f, app, app_hash)
	writeResults(app)	

if __name__ == '__main__':
	main()
