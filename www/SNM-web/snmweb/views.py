from pyramid.view import view_config
from pyramid.response import Response
from mongoengine import *
from db_objects import *


@view_config(route_name="overview", renderer='templates/overview.jinja2')
def view_overview(request):
    return {"status": "200 OK"}


@view_config(route_name="home", renderer='templates/index.jinja2')
def view_home(request):
    return {"status": "200 OK"}


@view_config(route_name="app_usage", renderer='templates/app_usage.jinja2')
def view_app_usage(request):
    name = request.matchdict["name"]
    app = Application.objects(title=name).first()
    return {"app": app}


@view_config(route_name="app_used_with", renderer='templates/app_used_with.jinja2')
def view_app_used_with(request):
    name = request.matchdict["name"]
    app = Application.objects(title=name).first()
    return {"app": app}


@view_config(route_name="application", renderer='templates/application.jinja2')
def view_application(request):
    name = request.matchdict["name"]
    app = Application.objects(title=name).first()
    return {"app": app}


@view_config(route_name="compare", renderer='templates/compare.jinja2')
def view_compare(request):
    return {"status": "200 OK"}


@view_config(route_name="data-sources", renderer='templates/data-sources.jinja2')
def view_data_sources(request):
    return {"status": "200 OK"}


@view_config(route_name="browse", renderer='templates/browse.jinja2')
def view_explore(request):
    try:
        order = request.params["order"]
    except:
        order = "usage"
    apps = Application.objects.order_by(order)
    return {"apps": apps}
