from pyramid.view import view_config
from pyramid.response import Response


@view_config(route_name="overview", renderer='templates/overview.jinja2')
def view_overview(request):
    return {}

@view_config(route_name="home", renderer='templates/index.jinja2')
def view_home(request):
    return {"status": "200 OK"}


@view_config(route_name="app_details", renderer='templates/app_details.jinja2')
def view_app_details(request):
    return { "name": request.matchdict["name"] }

@view_config(route_name="application", renderer='templates/application.jinja2')
def view_application(request):
    return { "name": request.matchdict["name"] }

@view_config(route_name="compare", renderer='templates/compare.jinja2')
def view_compare(request):
    return {}

@view_config(route_name="data-sources", renderer='templates/data-sources.jinja2')
def view_data_sources(request):
    return {}

@view_config(route_name="browse", renderer='templates/browse.jinja2')
def view_explore(request):
    return {}

