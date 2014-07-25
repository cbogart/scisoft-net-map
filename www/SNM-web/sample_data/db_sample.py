from snmweb.db_objects import *
import random
from random import randrange, randint
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


def generate_links(app_list):
    print("Generate random links")
    max_links = int(len(app_list) / 1.5)
    min_links = 1
    for app in app_list:
        links = []
        for link in random.sample(
                                app_list,
                                randint(min_links, max_links)):
            links.append(Link(app=link, power=randint(0, 350)))
        print app.title, "{} links".format(len(links))
        coo = CoOccurence(application = app,
                          links = links)
        coo.save()


def load_data(filename="db_sample.json", usage_path="sample_usage", usage_users_path="sample_usage_users"):
    print("Loading information from {}".format(filename))
    f = open(os.path.join(usage_path, "30-applications"))
    hash_list = f.readlines()
    all_apps = []
    with open(filename) as f:
        data = json.load(f)
        for a in data:
            app = Application(**a)
            hash = random.choice(hash_list)[:10]
            app.save()
            all_apps.append(app)
            field_data = {}
            for field in ["daily", "weekly", "monthly"]:
                usage = any_usage(usage_path, hash)
                stat = []
                print app.title, field,"\t{} enttries".format(len(usage[field]))
                for entry in usage[field]:
                    stat.append(ByDateStat(**entry))
                field_data[field] = stat
            usage = Usage(application = app, **field_data)
            usage.save()
    generate_links(all_apps)

def retrieve_data():
    print("Done:")
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
