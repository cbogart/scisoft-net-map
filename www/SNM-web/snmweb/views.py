from pyramid.view import view_config
from pyramid.response import Response


@view_config(route_name="overview", renderer='templates/overview.jinja2')
def view_overview(request):
    return {}

@view_config(route_name="home", renderer='templates/index.jinja2')
def view_home(request):
    return {}