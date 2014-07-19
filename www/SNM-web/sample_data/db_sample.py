from snmweb.db_objects import *
from random import randrange
import datetime
from datetime import datetime as dt
import json


def erase_data():
    print("Deleting existing information")
    for usage in Usage.objects:
        usage.delete()

    for app in Application.objects:
        app.delete()


def load_data(filename="db_sample.json"):
    print("Loading information from {}".format(filename))
    with open(filename) as f:
        data = json.load(f)
        for a in data:
            app = Application(**a)
            app.save()
            field_data = {}
            for field in ["daily", "weekly", "monthly"]:
                stat = []
                for entry in a["usage_{}".format(field)]:
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
    connect("snm-test")
    erase_data()
    load_data()
    retrieve_data()
