#!/usr/bin/python


import sys, time, os, json
from datetime import datetime as dt, timedelta

def daily(filename):
	def parsedt(str):
		time_struct = time.strptime(str, "%Y-%m-%d")
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
	delta = timedelta(days=1)
	dates, times = [], []
	while start <= end:
		str_repr = start.strftime("%Y-%m-%d")
		dates.append(str_repr)
		times.append(int(data.get(str_repr, 0)))
		start += delta
	json.dump({"dates":dates, "runs": times} ,nf)

def main():
	if len(sys.argv) < 2:
		print "Need one arg"
		exit(1)
	hash = sys.argv[1]
	daily("{}-daily.tsv".format(hash))


main()
