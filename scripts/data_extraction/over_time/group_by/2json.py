#!/usr/bin/python


import sys, time, os, json
from datetime import datetime as dt, timedelta

def jsonsify(filename, format, delta):
	def parsedt(str):
		time_struct = time.strptime(str, format)
		return dt.fromtimestamp(time.mktime(time_struct))

	data = {}
	f = open(filename, "r")
	fname, _ = os.path.splitext(filename)
	nf = open("{}.json".format(fname), "w")
	for line in f.readlines():
		date, count= line.strip().split(":")
		data[date] = count
	start, end = min(data.keys()), max(data.keys())
	start, end = parsedt(start), parsedt(end)
	delta = timedelta(**delta)
	dates, times = [], []
	while start < end+delta:
		dates.append(start.strftime("%Y-%m-%d"))
		str_repr = start.strftime(format)
		times.append(int(data.get(str_repr, 0)))
		start += delta
	json.dump({"dates":dates, "runs": times} ,nf)

def main():
	formats = {'daily'  : "%Y-%m-%d",
		   'weekly' : "%Y-%W"}
	kwargs = {'daily'  : {'days' : 1},
		  'weekly' : {'weeks': 1}}
	if len(sys.argv) < 3:
		print "hash [daily|weekly]"
		exit(1)
	hash = sys.argv[1]
	fmt = sys.argv[2]
	jsonsify("{}-{}.tsv".format(hash,fmt)
		, formats[fmt]
		, kwargs[fmt])


main()
