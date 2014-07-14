from mongoengine import *


class Tag(Document):
    text = StringField(required=True)


class Application(Document):
    title = StringField(required=True)
    description = StringField()
    image = StringField()
    version = FloatField()
    tags = ListField(ReferenceField(Tag))


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
