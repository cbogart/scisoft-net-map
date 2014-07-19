import sys
import os
import json
from db_objects import *

from pyramid.view import (
    view_config,
    view_defaults
)


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
            response["data"] = "#TODO: Return list of available api calls "
            return response

        try:  # TODO: Handle non existing path
            _id = matchdict.get("id")
            response["data"] = getattr(self, category)(request, _id)
            response["status"] = self.STATUS_OK
        except Exception,e:
            response["status"] = self.STATUS_ERROR
            response["data"] = str(e)

        return response

    def apps(self,request, app_id):
        """ Return list of applications available
        or find specific one "api/apps/:app"
        """
        if app_id is None:
            return [{"name": "app1"}, {"name": "app2"}, {"name": "app3"}]
        return {"id": app_id, "name": "app"}

    def stat(self,request, type):
        """ Return list of data sources available
        or find specific one "api/stat/:some_stat"
        """
        path = "snmweb/static/stat/"
        def usage_over_time(group_by="day", id=None, **kwargs):
            d = {"day": "daily",
                 "week": "weekly",
                 "month": "monthly"}
            group = d.get(group_by)
            if group is None:
                raise Exception("Group_by argument"
                                "should be one of {}".format(
                                [","].join(d.keys())))

            if id is None:
                raise Exception("Please specify application id")

            result = []
            for entry in Usage.objects(application__in=id.split(",")).all():
                result.append({"data": entry.to_mongo()[group],
                               "title": entry.application.title})
            return result

        def co_occurence(**kwargs):
            with open(os.path.join(path, "co_occurence", "data.json"), "r") as f:
                result = json.load(f)
            return result

        def force_directed(id=None):
            with open(os.path.join(path, "force_directed", "data.json"), "r") as f:
                result = json.load(f)
            return result

        def unknown_stat(*args, **kwargs):
            raise Exception("Unknown request type")

        if type is None:
            return [{"id": "over_time"}, {"id": "count_users"}]

        return locals().get(type, unknown_stat)(**request.params)
