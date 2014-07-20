from snmweb.db_objects import *
import random
from random import randrange
import datetime
from datetime import datetime as dt
import json
import os
import sys


def erase_data():
    print("Deleting existing information")
    for usage in Usage.objects:
        usage.delete()

    for app in Application.objects:
        app.delete()

def any_usage(usage_path, hash):
    result = {}
    for field in ["daily", "weekly", "monthly"]:
        with open(os.path.join(usage_path,
                               "{}-{}.json".format(hash, field))) as f:
            result[field] = json.load(f)["data"]
    return result


def load_data(filename="db_sample.json", usage_path="sample_usage"):
    print("Loading information from {}".format(filename))
    f = open(os.path.join(usage_path, "30-applications"))
    hash_list = f.readlines()
    with open(filename) as f:
        data = json.load(f)
        for a in data:
            app = Application(**a)
            hash = random.choice(hash_list)[:10]
            app.save()
            field_data = {}
            for field in ["daily", "weekly", "monthly"]:
                usage = any_usage(usage_path, hash)
                stat = []
                print app.title, field,10*"-"
                for entry in usage[field]:
                    print "\t", entry
                    stat.append(ByDateStat(**entry))
                field_data[field] = stat
            usage = Usage(application = app, **field_data)
            usage.save()

def retrieve_data():
    print("Retrieving information about applications and their usage")
    print("List of applications")
    for app in Application.objects:
        print " * ",app.title
	x = Usage.objects().count()
    print("Daily usage over time: {} entries loaded".format(x))

if __name__ == "__main__":
    db = "snm-test"
    if len(sys.argv) > 1:
        db = sys.argv[1]
    print "Using database: `{}`. You can specidy db with first argument".format(db)
    connect(db)
    erase_data()
    load_data()
    retrieve_data()
