from mongoengine import *


class Application(Document):
    title = StringField(required=True)
    description = StringField(required=True)
    short_description = StringField()
    image = StringField()
    version = StringField()
    usage = IntField()
    trend = IntField()
    website = StringField()


class ByDateStat(EmbeddedDocument):
    y = IntField()
    x = StringField()


class Usage(Document):
    application = ReferenceField(Application, required=True)
    daily = ListField(EmbeddedDocumentField(ByDateStat))
    weekly = ListField(EmbeddedDocumentField(ByDateStat))
    monthly = ListField(EmbeddedDocumentField(ByDateStat))


class UsersUsage(Document):
    application = ReferenceField(Application, required=True)
    daily = ListField(EmbeddedDocumentField(ByDateStat))
    weekly = ListField(EmbeddedDocumentField(ByDateStat))
    monthly = ListField(EmbeddedDocumentField(ByDateStat))


class Link(EmbeddedDocument):
    app = ReferenceField(Application, required=True)
    power = IntField()


class CoOccurence(Document):
    application = ReferenceField(Application, required=True)
    links = ListField(EmbeddedDocumentField(Link))
