from mongoengine import *

class GlobalStats(Document):
    max_co_uses = MapField(field=IntField())   # biggest number of times 2 packages used together ever (for scaling) (obs)
    max_publications = IntField()         # Biggest number of publications any software has seen (for scaling) (obs)
    last_r_packet = StringField()           # epoch of last R packet received
    last_git_project = StringField()        # epoch of last R packet received
    num_git_projects_total = IntField()      # Number of github projects seen
    num_git_projects_scraped = IntField()    # number of github project sampled

"""
This class represents collection with applications
"""
class Application(Document):
    title = StringField(required=True)
    description = StringField(required=True, default="")
    short_description = StringField(default="")
    image = StringField(default="unknown.jpg")
    repository = StringField(default="")
    version = StringField(default="")
    usage = IntField(default=0)
    usage_trend = IntField(default=0)
    users = IntField(default=0)
    git_usage = IntField(default=0)
    git_centrality = FloatField(default=0.0)
    website = StringField(default="")
    publications = IntField(default=0)
    publicationsUrl = StringField(default="")
    views = ListField(StringField())

"""
Just a list of task views; each is in the form repo/viewname,
e.g. cran/Optimization
"""
class Views(Document):
    viewname = StringField()

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

class VersionUsage(Document):
    application = ReferenceField(Application, required=True)
    version = StringField()
    daily = ListField(EmbeddedDocumentField(ByDateStat))
    weekly = ListField(EmbeddedDocumentField(ByDateStat))
    monthly = ListField(EmbeddedDocumentField(ByDateStat))

class VersionUsersUsage(Document):
    application = ReferenceField(Application, required=True)
    version = StringField()
    daily = ListField(EmbeddedDocumentField(ByDateStat))
    weekly = ListField(EmbeddedDocumentField(ByDateStat))
    monthly = ListField(EmbeddedDocumentField(ByDateStat))


"""
Same format as Usage, but records git projects, as one
project (or subproject) per usage, and the date is the
last update we've checked of that project.
"""
class GitUsage(Document):
    application = ReferenceField(Application, required=True)
    daily = ListField(EmbeddedDocumentField(ByDateStat))
    weekly = ListField(EmbeddedDocumentField(ByDateStat))
    monthly = ListField(EmbeddedDocumentField(ByDateStat))


"""
Actual git projects that refer to Git, CRAN, or Bioconductor packages.
"""
class GitReferers(Document):
    url = StringField()
    name = StringField()
    owner = StringField()
    description = StringField()
    created_at= StringField()
    forked_from= StringField()
    cb_last_scan= StringField()
    pushed_at= StringField()
    watchers_count= StringField()
    stargazers_count= StringField()
    forks_count= StringField()
    dependencies = ListField(StringField())

"""
Same format as Usage, but this is for overall stats about
the data sources for the site: how many R sessions have been
recorded (category="R sessions"); how many Git projects have
been scraped (category = "Github projects"); how many R packages
have been downloaded from R studio's cran mirror (category =
"R studio downloads")
"""
class SystemUsage(Document):
    category = StringField()
    daily = ListField(EmbeddedDocumentField(ByDateStat))
    weekly = ListField(EmbeddedDocumentField(ByDateStat))
    monthly = ListField(EmbeddedDocumentField(ByDateStat))


""" 
Same format as UsersUsage, but capturing total overall data
sources; see SystemUsage for the values of category.
"""
class SystemUsersUsage(Document):
    category = StringField()
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
Same as CoOccurenceLinks, but taken from Github project
data
"""
class GitCoOccurenceLinks(Document):
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
    doi=StringField()
    canonical=BooleanField()
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

class GitProjects(Document):
    user = StringField()
    jobID = StringField()
    lastUpdateEpoch = StringField()
    pkgT = DictField()

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
