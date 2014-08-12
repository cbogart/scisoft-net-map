#!/usr/bin/python
#
# Authors:
#  Chris Bogart, Nikita Chepanov, Biao "Leo" Ma, Svyatoslav "Slava" Kovtunenko
#
import json
import sys
import os
import datetime
import time
import math
from collections import defaultdict
from datetime import date, timedelta
from os import walk
from snmweb.db_objects import *

def enoughUsers(app, userThreshhold):
    users = set()
    for bydateusers in UserList.objects(application=app).first().users:
        users.update(set(bydateusers.users))
        if len(users) >= userThreshhold:
            return True
    return len(users) >= userThreshhold

def populate(dbProduction, dbStaging, userThreshhold=5):
    legit = dict()
    # Determine "legit" applications (more then 5 users)
    for app in Application.objects:
        if enoughUsers(app, userThreshhold):
            legit[app.name] = app

    db.sister
    # Copy Application() table, filter to legit ones
    # fill in Application statistics
    # look up application data in app_info.json
    # Copy usage and users_usage over for legit applications
    # compute weekly and monthly data streams for usage
    # compute users_usage from UserList
    # Copy over legit portions of CoOccurence() table

if __name__ == "__main__":
    dbProduction = "snm-web"
    dbStaging = "snm-staging"
    mongoProd = connect(dbProduction, alias="prod")
    mongoStage = connect(dbStaging, alias="stage")
    print "All data from `{}` will be erased.".format(dbStaging)
    raw_input("Press Enter to continue...")
    # TO DO: eventually we will not drop database, but instead be careful never to
    # put data in it twice, and make it just add one or more lariat records incrementally
    mongoProd.drop_database(dbProduction)
    populate(dbProduction, dbStaging, userThreshhold=5)
    #retrieve_data()
