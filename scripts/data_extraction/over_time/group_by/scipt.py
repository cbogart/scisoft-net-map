#!/usr/bin/python

import json, sys, os 
import datetime, time
import collections
from datetime import date, timedelta
from os import walk

class App:
	def __init__(self, hash ):
		self.hash = hash
		self.daily= collections.defaultdict(int)
		self.weekly = collections.defaultdict(int)
		self.monthly= collections.defaultdict(int)

	def addRun(self, run):
		dt = datetime.datetime.fromtimestamp(float(run["startEpoch"])).date()
		# the day
		day = dt.__str__()
		self.daily[day] += 1
		# nearest 
		week = dt + datetime.timedelta(days=-dt.weekday(), weeks=1)
		week = week.__str__()
		self.weekly[week] += 1
		
		# Month first day
		month = date(dt.year, dt.month, 1).__str__()
		self.monthly[month] += 1
	def fill_empty_dates(self):
		def parsedt(str):
			time_struct = time.strptime(str, "%Y-%m-%d")
			return datetime.datetime.fromtimestamp(time.mktime(time_struct))
		# yet by day only
		data = self.daily
		start, end = min(data.keys()), max(data.keys())
		start, end = parsedt(start), parsedt(end)
		delta = timedelta(days=1)
		while start < end+delta:
			str_repr = start.strftime("%Y-%m-%d")
			self.daily[str_repr] = int(data.get(str_repr, 0))
			start += delta
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
	app.fill_empty_dates()
	j = {
	  "id"	: "",
	  "data": [ ]
	}
	for prop in ['daily', 'weekly', 'monthly']:
		j["id"] = app.hash
		j["data"] = [{"x":k, "y": v} for k,v in getattr(app,prop).iteritems()]
		f = open("{}-{}.json".format(app.hash[:10], prop), 'w')
		json.dump(j, f)
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
