from mongoengine import *

"""
This class represents collection with applications
"""
class Application(Document):
    title = StringField(required=True)
    description = StringField(required=True)
    short_description = StringField()
    image = StringField()
    version = StringField()
    usage = IntField()
    trend = IntField()
    website = StringField()

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
    power = IntField()


"""
This collection stores applications that happened to co-occur with given
application.
    /api/stat/force_directed
"""
class CoOccurence(Document):
    application = ReferenceField(Application, required=True)
    links = ListField(EmbeddedDocumentField(Link))
