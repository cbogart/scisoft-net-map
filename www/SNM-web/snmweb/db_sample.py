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
    euler.description = "Euler (now Euler Mathematical Toolbox or EuMathT) is a free and open-source numerical software package. It contains a matrix language, a graphical notebook style interface, and a plot window. Euler is designed for higher level math such as calculus, optimization, and statistics. The software can handle real, complex and interval numbers, vectors and matrices, it can produce 2D/3D plots, and uses Maxima for symbolic operations. The software is compilable with Windows. The Unix and Linux versions do not contain a computer algebra subsystem."
    euler.image  = "euler.png"
    euler.version = 2.5
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
