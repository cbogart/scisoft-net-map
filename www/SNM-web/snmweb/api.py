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
        return {"id": app_id,
                "name": "app"}

    def stat(self,request, type):
        """ Return list of data sources available
        or find specific one "api/stat/:some_stat"
        """
        def usage_over_time(group_by='day', id=None, **kwargs):
            if id is None:
                raise Exception("Please specify application id")
            id = id.split(",")
            group = {'day':'daily', 'week':'weekly', 'month':'monthly'}[group_by]
            # TODO: substitute with db query
            path = "snmweb/static/stat/usage_over_time"
            result = []
            for i in id:
                filename = "{}-{}.json".format(i, group)
                with open(os.path.join(path, filename), 'r') as f:
                    result.append(json.load(f))
            return result

        def co_occurence(**kwargs):
            path = "snmweb/static/stat/co_occurence"
            with open(os.path.join(path, "data.json"), 'r') as f:
                    result = json.load(f)
            return result

        def unknown_stat(*args, **kwargs):
            raise Exception('Unknown request type')

        if type is None:
            return [{"id": "over_time"}, {"id": "count_users"}]

        return locals().get(type, unknown_stat)(**request.params)
