from mongoengine import *


class Tag(Document):
    text = StringField(required=True)


class Application(Document):
    title = StringField(required=True)
    description = StringField(required=True)
    short_description = StringField()
    image = StringField()
    version = StringField()
    tags = ListField(ReferenceField(Tag))


#TODO:
"""
Data should be restructured in the following way
(check ../sample_date/db_sample.json for details)
class TypeOfStat(Document):
    app = ReferenceField(Application, required=True)
    daily = ListField(of key-value pairs: date <-> value)
    weekly = = ListField(of key-value pairs: date <-> value)
    monthly = ListField(of key-value pairs: date <-> value)

This is how we can get required data in one query.
But we're loosing query by time period capabilities.
"""
class UsageOverTimeDaily(Document):
    application = ReferenceField(Application, required=True)
    date = DateTimeField(required=True)
    value = IntField(required=True)


class UsageOverTimeWeekly(Document):
    application = ReferenceField(Application, required=True)
    date = DateTimeField(required=True)
    value = IntField(required=True)


class UsageOverTimeMonthly(Document):
    application = ReferenceField(Application, required=True)
    date = DateTimeField(required=True)
    value = IntField(required=True)
