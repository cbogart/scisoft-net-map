from mongoengine import *

class GlobalStats(Document):
    max_co_uses = MapField(field=IntField())
    max_publications = IntField()

"""
This class represents collection with applications
"""
class Application(Document):
    title = StringField(required=True)
    description = StringField(required=True, default="")
    short_description = StringField(default="")
    image = StringField(default="unknown.jpg")
    version = StringField(default="")
    usage = IntField()
    usage_trend = IntField()
    users = IntField()
    website = StringField(default="")
    publications = IntField()
    publicationsUrl = StringField(default="")

"""
This class represents nested structure that looks like this:

    {
        "y" : 100,
        "x" : "some date here"
    }
"""
class ByDateStat(EmbeddedDocument):
    y = IntField()
    x = StringField()

"""
For a given application this collection can return information about
weekly/daily/monthly usage, where each is a list of the class above,
for example:

    "weekly": [
                {
                    "x": ...,
                    "y": ...
                },
                {...},
                {...},
                ...
            ]
Can be queried with the following api call:
    /api/stat/usage_over_time
"""
class Usage(Document):
    application = ReferenceField(Application, required=True)
    daily = ListField(EmbeddedDocumentField(ByDateStat))
    weekly = ListField(EmbeddedDocumentField(ByDateStat))
    monthly = ListField(EmbeddedDocumentField(ByDateStat))

"""
Similar to the above, this collection stores number of users
Can be retrieved with the following api call:
    /api/stat/users_over_time
"""
class UsersUsage(Document):
    application = ReferenceField(Application, required=True)
    daily = ListField(EmbeddedDocumentField(ByDateStat))
    weekly = ListField(EmbeddedDocumentField(ByDateStat))
    monthly = ListField(EmbeddedDocumentField(ByDateStat))


"""
This structure represents a single linked application with its weight,
for example:
{
    "app": app_id_here,
    "weight" : 100
}

"""
class Link(EmbeddedDocument):
    app = ReferenceField(Application, required=True)
    co_uses = MapField(field=IntField())


"""
This structure represents a flat list of all links between
applications, with absolute counts of co-usages (static and logical)

   focal: reference to an application
   other: reference to an application
   type: upstream, downstream, or usedwith (or other)
   count: raw count
   countDivTarget: count/target app count
   
Note that every link will appear twice, with focal and other reversed,
and only the countDivTarget value will be different.
The list should be sorted by countDivTarget (descending).

force_directed api should return the top N values matching focal.
The Nth one becomes a threshhold.
Then search all the N "other" apps found, each as focal, 
returning all the ones whose countDivTarget > that threshhold.
"""
class CoOccurenceLinks(Document):
    focal = ReferenceField(Application, required=True)
    other = ReferenceField(Application, required=True)
    type = StringField(required=True)
    raw_count = IntField(required=True)
    scaled_count = FloatField()

"""
User logins: these are for people logging into the web service,
not users of the scientific software being tracked.
Password is encrypted using passlib
"""
class WebUsers(Document):
    userid = StringField(required=True)
    password = StringField(required=True)


"""
This collection stores applications that happened to co-occur with given
application.
    /api/stat/force_directed
"""
class CoOccurence(Document):
    application = ReferenceField(Application, required=True)
    links = ListField(EmbeddedDocumentField(Link))

"""
This collection stores applications that are strictly dependent on given
application.
class Dependency(Document):
    application = ReferenceField(Application, required=True)
    links = ListField(EmbeddedDocumentField(Link))
"""

"""
----------Working tables------------------
Hold data that is not used by the website, but for calculating
incremental updates to website data
------------------------------------------
"""

"""
ByDateDetails: nested structure for holding a list of users or publications or whatever, associated with a date

    {
        "items" : List of strings
        "date" : "some date here"
    }
"""

class ByDateUsers(EmbeddedDocument):
    users = ListField(StringField(), required=True)
    date = StringField()

class PubInfo(DynamicEmbeddedDocument):
    title=StringField()
    year=StringField()
    url=StringField()

"""
UserList: List of users by date for each app.  We need this to
calculate the number of distinct users in each time period
"""
class UserList(Document):
    application = ReferenceField(Application, required=True)
    users = ListField(EmbeddedDocumentField(ByDateUsers))

class PubList(Document):
    application = ReferenceField(Application, required=True)
    publications = ListField(EmbeddedDocumentField(PubInfo))



"""
Raw Records: Provide access to the raw records recieved directly
from R client. Not all fields are captured here; just the ones
the api module needs to serve them up.
"""
class RawRecords(Document):
    user = StringField()
    startTime = StringField()
    startEpoch = StringField()
    endTime = StringField()
    endEpoch = StringField()
    userMetadata = DictField()
    jobID = StringField()
    platform = DictField()
    pkgT = DictField()
    meta = {"db_alias": "raw-records", "collection": "scimapInfo"}
