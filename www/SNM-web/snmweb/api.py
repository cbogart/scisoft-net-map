import sys

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

    def apps(request, app_id):
        """ Return list of applications available
        or find specific one "api/apps/:app"
        """
        if app_id is None:
            return [{"name": "app1"}, {"name": "app2"}, {"name": "app3"}]
        return {"id": app_id,
                "name": "app" + app_id}

    def viz(request, viz_id):
        """ Return list of data sources available
        or find specific one "api/apps/:app"
        """
        if viz_id is None:
            return [{"id": "over_time"}, {"id": "count_users"}]
        if viz_id == "usage_over_time":
            return "this is faked data"
        raise Exception('No visualization {} found'.format(viz_id))