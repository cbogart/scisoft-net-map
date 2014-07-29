from snmweb.db_objects import *
import random
import datetime
from random import randrange, randint
from datetime import datetime as dt
import json
import os
import sys


def any_usage(usage_path, hash):
    result = {}
    for field in ["daily", "weekly", "monthly"]:
        with open(os.path.join(usage_path,
                               "{}-{}.json".format(hash, field))) as f:
            result[field] = json.load(f)["data"]
    return result


def generate_links(app_list):
    print("Generate random links")
    max_links = 3
    min_links = 0
    l = len(app_list)
    links = [[False] * l for i in range(l)] # the matrix
    for _ in range(int(l*1.3)): #total number of links
        i, j = randint(0, l-1), randint(0, l-1)
        links[i][j] = links[j][i] = True

    for idx, app in enumerate(app_list):
        app_links = []
        for idx2, linked in enumerate(links[idx]):
            if not linked: continue
            if idx == idx2: continue
            app_links.append(Link(app=app_list[idx2], power=randint(1, 10)))
        print app.title, "{} links".format(len(app_links))
        coo = CoOccurence(application=app,
                          links=app_links)
        coo.save()


def load_apps(filename):
    print("Loading information from {}".format(filename))
    all_apps = []
    with open(filename) as f:
        data = json.load(f)
        for a in data:
            app = Application(**a)
            app.save()
            all_apps.append(app)
    return all_apps


def load_stat(app, hash, dir_path, stat_type):
    field_data = {}
    for field in ["daily", "weekly", "monthly"]:
        usage = any_usage(dir_path, hash)
        stat = []
        print app.title, field, "\t{} entries".format(len(usage[field]))
        for entry in usage[field]:
            stat.append(ByDateStat(**entry))
        field_data[field] = stat
    stat_obj = globals()[stat_type](application=app, **field_data)
    stat_obj.save()


def load_usage_summary(app):
    app_usage = 0
    app_trend = 0
    usage = Usage.objects(application=app).first()
    if usage is not None:
        for entry in usage.daily:
            date = dt.strptime(entry.x, "%Y-%m-%d")
            current_date = datetime.datetime(2013, 1, 27)  #should be current date, for now the last date we have data
            if (current_date - date).days < 60:
                app_trend += entry.y
            app_usage += entry.y
        app.usage = app_usage
        app.trend = app_trend
        app.save()


def load_data(filename="db_sample.json",
              hash_file_path="sample_usage/21-applications",
              usage_path="sample_usage",
              usage_users_path="sample_usage_users"):
    all_apps = load_apps(filename)
    f = open(hash_file_path)
    hash_list = f.readlines()
    hash_iterator = iter(hash_list)
    for app in all_apps:
        hash = hash_iterator.next()[:10]
        load_stat(app, hash, usage_path, "Usage")
        load_usage_summary(app)
        load_stat(app, hash, usage_users_path, "UsersUsage")
    generate_links(all_apps)


def retrieve_data():
    print("Done:")
    for app in Application.objects:
        print " * ", app.title
        x = Usage.objects().count()
    print("Done: {} sample applications loaded".format(x))


if __name__ == "__main__":
    db = "snm-test"
    if len(sys.argv) > 1:
        db = sys.argv[1]
    print "Using database: `{}`. You can specidy db with first argument".format(db)
    mongo = connect(db)
    print "All data from `{}` will be erased.".format(db)
    raw_input("Press Enter to continue...")
    mongo.drop_database(db)
    load_data()
    retrieve_data()
