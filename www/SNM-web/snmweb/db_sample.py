from mongoengine import *
from db_objects import *
import datetime


def EraseData():
    print("Deleting existing information")
    for usage in UsageOverTimeDaily.objects:
        usage.delete()

    for app in Application.objects:
        app.delete()


def LoadData():
    print("Loading information about Euler")
    euler = Application(title="Euler")
    euler.description = "Euler description"
    image = "euler.png"
    version = 2.5
    euler.save()

    eulerUsageDaily = UsageOverTimeDaily()
    eulerUsageDaily.application = euler
    eulerUsageDaily.date = datetime.datetime.now()
    eulerUsageDaily.value = 111
    eulerUsageDaily.save()


def RetrieveData():
    print("Retrieving information about applications and their usage")
    print("List of applications")
    for app in Application.objects:
        print app.title

    euler = Application.objects[0]
    print("Daily usage over time of Euler")
    for usage in UsageOverTimeDaily.objects(application=euler):
        print usage.value


if __name__ == "__main__":
    connect("snm-test")
    EraseData()
    LoadData()
    RetrieveData()
