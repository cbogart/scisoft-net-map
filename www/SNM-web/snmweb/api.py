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
        except Exception, e:
            response["status"] = self.STATUS_ERROR
            response["data"] = str(e)

        return response

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
        path = "snmweb/static/stat/"

        def usage_over_time(group_by="day", id=None, **kwargs):
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
            for entry in Usage.objects(application__in=id.split(",")).all():
                result.append({"data": entry.to_mongo()[group],
                               "title": entry.application.title})
            return result

        def co_occurence(id=None):
            if id is None:
                raise Exception("Please, specify application id")
            app = Application.objects.get(id=id)
            cooc = CoOccurence.objects.get(application=id)
            nodes = [{"name": app.title, "id": app.id.__str__()}]
            links = []
            reverse_dict = {app.id: 0}
            i = 1
            for l in cooc.links:
                nodes.append({"name": l.app.title, "id": l.app.id.__str__()})
                reverse_dict[l.app.id] = i
                i += 1
            for l in cooc.links:
                links.append({
                    "source": 0,
                    "target": reverse_dict[l.app.id],
                    "value": l.power
                })

            return {"nodes": nodes, "links": links}

        def force_directed(id=None):
            return co_occurence(id)

        def unknown_stat(*args, **kwargs):
            raise Exception("Unknown request type")

        if type is None:
            return [{"id": "over_time"}, {"id": "count_users"}]

        return locals().get(type, unknown_stat)(**request.params)
