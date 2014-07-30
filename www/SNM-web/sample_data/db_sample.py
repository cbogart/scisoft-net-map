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


def load_distinct_users_number(app, hash, usage_users_path):
    with open(os.path.join(usage_users_path,
                           "{}-{}.json".format(hash, "daily"))) as f:
        app.users = json.load(f)["users"]
        app.save()


def load_usage_summary(app):
    def load_internal(stat):
        if stat is not None:
            usage = 0
            trend = 0
            for entry in stat.daily:
                date = dt.strptime(entry.x, "%Y-%m-%d")
                current_date = datetime.datetime(2013, 1, 27)  #should be current date, for now the last date we have data
                if (current_date - date).days < 60:
                    trend += entry.y
                usage += entry.y
            return (usage, trend)

    usage = Usage.objects(application=app).first()
    app_usage, app_usage_trend = load_internal(usage)
    app.usage = app_usage
    app.usage_trend = app_usage_trend
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
        load_stat(app, hash, usage_users_path, "UsersUsage")
        load_distinct_users_number(app, hash, usage_users_path)
        load_usage_summary(app)
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
