import sys
import os
import json

from pyramid.view import (
    view_config,
    view_defaults
)


@view_defaults(renderer='json')
class ApiViews:
    def __init__(self, request):
        self.request = request
        self.TEMPLATE = {"version": 0.1,
                         "status": None,
                         "data": None}
        self.STATUS_OK = "OK"
        self.STATUS_ERROR = "ERROR"

    @view_config(route_name='api_home')
    @view_config(route_name='api_home.category')
    @view_config(route_name='api_home.category.id')
    def home(self):
        request = self.request
        response = self.TEMPLATE.copy()
        matchdict = request.matchdict
        category = matchdict.get("category")

        if category is None:
            return response

        try:  # TODO: Handle non existing path
            _id = matchdict.get("id")
            response["data"] = getattr(self, category)(request, _id)
            response["status"] = self.STATUS_OK
        except:
            e = sys.exc_info()[0]  # TODO: Specify different types of exceptions
            response["status"] = self.STATUS_ERROR
            response["data"] = str(e)

        return response

    def apps(self,request, app_id):
        """ Return list of applications available
        or find specific one "api/apps/:app"
        """
        if app_id is None:
            return [{"name": "app1"}, {"name": "app2"}, {"name": "app3"}]
        return {"id": app_id,
                "name": "app" }

    def stat(self,request, type):
        """ Return list of data sources available
        or find specific one "api/stat/:some_stat"
        """
        def usage_over_time(group_by='day', **kwargs):
            # TODO: substitute with db query
            path = "snmweb/static/stat/usage_over_time"
            filename = "group_by_{}.json"
            with open(os.path.join(path, filename.format(group_by)), 'r') as f:
                data = json.load(f)
            return data

        def unknown_stat(*args, **kwargs):
            raise Exception('Unknown request type')

        if type is None:
            return [{"id": "over_time"}, {"id": "count_users"}]

        return locals().get(type, unknown_stat)(**request.params)
