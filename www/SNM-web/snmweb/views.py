from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPClientError
from pyramid.security import Authenticated, remember, forget
from mongoengine import *
from db_objects import *
from passlib.apps import custom_app_context as pwd_context
from pyramid.view import forbidden_view_config

def count_visits(request):
    visits=int(request.cookies.get('visits', "0"))+1
    request.response.set_cookie('visits', value=str(visits), max_age=1000000)
    return(visits)

@view_config(route_name="overview",
             renderer='templates/overview.jinja2')
def view_overview(request):
    return {"status": "200 OK", "visits": count_visits(request)}

@view_config(route_name="dsm",
             renderer='templates/dsm.jinja2',
             permission='view')
def view_dsm(request):
    return {"status": "200 OK", "visits": count_visits(request)}

@view_config(route_name="home",
             renderer='templates/index.jinja2',
             permission='view')
def view_home(request):
    return {"status": "200 OK", "visits": count_visits(request)}

@view_config(route_name="app_usage",
             renderer='templates/app_usage.jinja2',
             permission='view')
def view_app_usage(request):
    name = request.matchdict["name"]
    app = Application.objects(title=name).first()
    return {"app": app, "visits": count_visits(request)}


@view_config(route_name="app_users",
             renderer='templates/app_users.jinja2',
             permission='view')
def view_app_users(request):
    name = request.matchdict["name"]
    app = Application.objects(title=name).first()
    return {"app": app, "visits": count_visits(request)}

@view_config(route_name="app_pubs",
             renderer='templates/app_pubs.jinja2',
             permission='view')
def view_app_pubs(request):
    name = request.matchdict["name"]
    app = Application.objects(title=name).first()
    publist = PubList.objects(application=app).first()

    return {"app": app, "pubs": publist, "visits": count_visits(request)}

@view_config(route_name="app_used_with",
             renderer='templates/app_used_with.jinja2',
             permission='view')
def view_app_used_with(request):
    name = request.matchdict["name"]
    app = Application.objects(title=name).first()
    return {"app": app, "visits": count_visits(request)}

@view_config(route_name="application",
             renderer='templates/application.jinja2',
             permission='view')
def view_application(request):
    name = request.matchdict["name"]
    app = Application.objects(title=name).first()
    return {"app": app, "visits": count_visits(request)}


@view_config(route_name="compare",
             renderer='templates/compare.jinja2',
             permission='view')
def view_compare(request):
    return {"status": "200 OK", "visits": count_visits(request)}

@view_config(route_name="about",
             renderer='templates/about.jinja2')
def view_about(request):
    return {"status": "200 OK", "visits": count_visits(request)}

@view_config(route_name="data_source",
             renderer='templates/data_source.jinja2')
def view_data_source(request):
    return {"status": "200 OK", "visits": count_visits(request)}

@forbidden_view_config()
def view_forbidden(request):
    return HTTPFound(location=request.route_url('login'))

@view_config(route_name="login",
             renderer='templates/login.jinja2')
def view_login(request):
    return {"status": "200 OK"}

@view_config(route_name="accept_login",
             renderer='templates/overview.jinja2')
def view_accept_login(request):
    try:
        userid = request.params.get('userid')
        password = request.params.get('password')
        users = WebUsers.objects(userid=userid)
        if(len(users) > 0 and pwd_context.verify(password, users[0].password)):
            print "apparently a match"
            headers = remember(request, userid)
            return HTTPFound(location = request.route_url('home'),
                                 headers =headers)
        else:
            return HTTPClientError("Login failure")
    except Exception as e:
        return HTTPClientError(str(e))

@view_config(route_name="browse",
             renderer='templates/browse.jinja2',
             permission='view')
def view_explore(request):
    order = request.params.get("order", "usage")
    query = request.params.get("query", "")
    apps = Application.objects(title__icontains=query).order_by(order)
    return {"apps": apps, "visits": count_visits(request)}
