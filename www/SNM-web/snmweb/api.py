import os
import json
import sys
from db_objects import *
from pymongo import Connection

from pyramid.view import (
    view_config,
    view_defaults
)

"""

All API calls have the following structure:
/api/:category/:id

For example: /api/apps/MyApp

In order to add new category just add new method in ApiViews class.
Both def apps(), def stat() can be used as reference point

For a given category nested functions are defined in order to address
different calls within category.
For example: /api/stat/usage_over_time is defined as
def usage_over_time() under def stat()

In order to add new type of data you can simply define new nested function
and process user request in it.
"""
@view_defaults(renderer="json")
class ApiViews:
    def __init__(self, request):
        self.request = request
        self.TEMPLATE = {"version": 0.1,
                         "status": None,
                         "data": None}
        self.STATUS_OK = "OK"
        self.STATUS_ERROR = "ERROR"

    @view_config(route_name="api_home")
    @view_config(route_name="api_home.category")
    @view_config(route_name="api_home.category.id")
    def home(self):
        request = self.request
        response = self.TEMPLATE.copy()
        matchdict = request.matchdict
        category = matchdict.get("category")

        if category is None:
            response["status"] = self.STATUS_OK
            response["data"] = repr(request)
            return response

        try:  # TODO: Handle non existing path
            _id = matchdict.get("id")
            response["data"] = getattr(self, category)(request, _id)
            response["status"] = self.STATUS_OK
        except Exception, e:
            response["status"] = self.STATUS_ERROR
            response["data"] = str(e)

        return response

    def register(self, request, type):
        """ Register a user's use of an application,
        dropping the information into a mongo collection.
        Parameters are ignored.
        """
        c = Connection()
        rawrecords = c["snm-raw-records"]
        record = json.loads(request.body)
        rawrecords["lariat"].save(record)
        return "Registered"

    def apps(self, request, type):
        """ Return list of applications available
        or find specific one "api/apps/:app"
        """

        def list(ids=None, query=None):
            result = []
            apps = []
            if not (ids is None) and not (query is None):
                apps = Application.objects(
                    Q(title__icontains=query) &
                    Q(id__in=ids.split(","))
                ).all()
            elif (ids is None) and not (query is None):
                apps = Application.objects(title__icontains=query).all()
            elif not (ids is None) and (query is None):
                apps = Application.objects(id__in=ids.split(",")).all()
            else:
                apps = Application.objects().all()

            for app in apps:
                result.append({
                    "id": str(app.id),
                    "name": app.title,
                    "link": request.route_url('application', name=app.title)
                })
            return result

        return list(**request.params)

    def stat(self, request, type):
        """ Return list of data sources available
        or find specific one "api/stat/:some_stat"
        """
        def data_over_time(group_by, id, stat_type):
            d = {"day": "daily",
                 "week": "weekly",
                 "month": "monthly"}
            group = d.get(group_by)
            if group is None:
                raise Exception("Group_by argument "
                                "should be one of {}".format(
                                    ",".join(d.keys())))

            if id is None:
                raise Exception("Please specify application id")

            result = []
            stat_object = globals()[stat_type]
            for entry in stat_object.objects(application__in=id.split(",")).all():
                result.append({"data": entry.to_mongo()[group],
                               "title": entry.application.title})
            return result

        def usage_over_time(group_by="day", id=None):
           return data_over_time(group_by, id, "Usage")


        def users_over_time(group_by="day", id=None):
            return data_over_time(group_by, id, "UsersUsage")

        def force_directed(id=None):
            nodes = []
            links = []

            if id is None:
                cooc = CoOccurence.objects()
            else:
                app = Application.objects.get(id=id)
                cooc = [CoOccurence.objects.get(application=id)]
                app_id = app.id.__str__()
                nodes.append({"name": app.title,
                              "id": app_id,
                              "publications": app.publications,
                              "link": request.route_url('application',
                                                        name=app.title)})
            for c in cooc:
                app_id = c.application.id.__str__()
                nodes.append({"name": c.application.title,
                              "id": app_id,
                              "publications": c.application.publications,
                              "link": request.route_url('application', name=c.application.title)})
                for l in c.links:
                    nodes.append({"name": l.app.title,
                                  "id": l.app.id.__str__(),
                                  "publications": l.app.publications,
                                  "link": request.route_url('application', name=l.app.title)})
                for l in c.links:
                    links.append({
                        "source": app_id,
                        "target": l.app.id.__str__(),
                        "value": l.power
                    })
            return {"nodes": nodes, "links": links}

        def unknown_stat(*args, **kwargs):
            raise Exception("Unknown request type")

        if type is None:
            return [{"id": "usage_over_time"},
                    {"id": "users_over_time"},
                    {"id": "force_directed"}]

        return locals().get(type, unknown_stat)(**request.params)
