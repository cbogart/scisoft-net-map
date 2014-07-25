from snmweb.db_objects import *
import random
import datetime
from random import randrange, randint
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
        coo = CoOccurence(application=app,
                          links=links)
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


def load_data(filename="db_sample.json", hash_file_path="sample_usage/30-applications", usage_path="sample_usage",
              usage_users_path="sample_usage_users"):
    all_apps = load_apps(filename)
    f = open(hash_file_path)
    hash_list = f.readlines()
    for app in all_apps:
        hash = random.choice(hash_list)[:10]
        load_stat(app, hash, usage_path, "Usage")
        load_usage_summary(app)
        load_stat(app, hash, usage_users_path, "UsersUsage")
    generate_links(all_apps)


def retrieve_data():
    print("Done:")
    for app in Application.objects:
        print " * ", app.title
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
