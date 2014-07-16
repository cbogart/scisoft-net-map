from snmweb.db_objects import *
from datetime import datetime as dt
import json
import sys


def erase_data():
    print("Deleting existing information")
    for usage in UsageOverTimeDaily.objects:
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
            for entry in a["usage_over_time"]:
                ud = UsageOverTimeDaily(
                    date=dt.strptime(entry["x"], "%Y-%m-%d"),
                    value=entry["y"],
                    application=app)
                ud.save()


def retrieve_data():
    print("Retrieving information about applications and their usage")
    print("List of applications")
    for app in Application.objects:
        print " * ", app.title
    x = UsageOverTimeDaily.objects().count()
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
