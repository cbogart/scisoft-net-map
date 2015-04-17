from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPClientError
from pyramid.security import Authenticated, remember, forget
from mongoengine import *
from db_objects import *
from status import check_site_status
from passlib.apps import custom_app_context as pwd_context
from pyramid.view import forbidden_view_config
import time

def count_visits(request):
    try:
        visits=int(request.cookies.get('visits', "0"))+1
    except Exception, e:
        print("Error reading visit cookie: visits=" + request.cookies.get('visits',"0"))
        visits = 1
    request.response.set_cookie('visits', value=str(visits), max_age=1000000)
    return(visits)

def cached_scimapID(request):
    scimapID = request.params.get("scimapID", request.cookies.get('scimapID', ""))
    request.response.set_cookie("scimapID", value=scimapID, max_age=1000000)
    return scimapID

@view_config(route_name="overview",
             renderer='templates/overview.jinja2')
def view_overview(request):
    return {"status": "200 OK", "visits": count_visits(request), "scimapID": cached_scimapID(request)}

@view_config(route_name="dsm",
             renderer='templates/dsm.jinja2',
             permission='view')
def view_dsm(request):
    return {"status": "200 OK", "visits": count_visits(request)}

@view_config(route_name="notebook",
             renderer='templates/notebook.jinja2',
             permission='view')
def view_notebook(request):
    scimapID = cached_scimapID(request)
    entries = RawRecords.objects(user=scimapID)
    return {"status": "200 OK", "entries": entries, "visits": count_visits(request), "scimapID": scimapID}

@view_config(route_name="status", permission='view')
def view_status(request):
    site_status = check_site_status(request.registry.settings.get("sci_platform", "R"))
    return Response(site_status)

@view_config(route_name="home",
             renderer='templates/index.jinja2',
             permission='view')
def view_home(request):
    featured = Application.objects(title=request.registry.settings.get("featured")).first()
    return {"status": "200 OK", "featured": featured, "visits": count_visits(request), "scimapID": cached_scimapID(request)}

@view_config(route_name="app_dashboard",
             renderer='templates/app_dashboard.jinja2',
             permission='view')
def view_dashboard(request):
    name = request.matchdict["name"]
    app = Application.objects(title=name).first()
    return {"app": app, "visits": count_visits(request)}

@view_config(route_name="app_usage",
             renderer='templates/app_usage.jinja2',
             permission='view')
def view_app_usage(request):
    name = request.matchdict["name"]
    app = Application.objects(title=name).first()
    return {"app": app, "visits": count_visits(request)}


@view_config(route_name="sys_usage",
             renderer='templates/sys_usage.jinja2',
             permission='view')
def view_sys_usage(request):
    gs = GlobalStats.objects().first()
    return {"visits": count_visits(request),
            "git_projects": gs.num_git_projects_scraped,
            "r_sessions": RawRecords.objects().count(),
            #"r_users": 6,
            "repositories": Application.objects().item_frequencies('repository'),                          
            #"earliest_git_update": "Mon Mar 23 2015",
            #"earliest_r_update": RawRecords.objects().first()["receivedEpoch"],   #%B %d, %Y %H:%M:%S %Z"
            "latest_git_update": time.strftime("%c %Z" , time.localtime(float(gs.last_git_project))),
            "latest_r_packet": time.strftime("%c %Z", time.localtime(float(gs.last_r_packet)))}


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

@view_config(route_name="app_gitprojects",
             renderer='templates/app_gitprojects.jinja2',
             permission='view')
def view_app_gitprojects(request):
    name = request.matchdict["name"]
    app = Application.objects(title=name).first()
    total_git_referers = GitReferers.objects(dependencies= name.replace("[dot]",".")).count()
    
    try:
       start_at = int(request.params.get("start-at"))
    except:
       start_at = 1
    if (start_at < 1): start_at = 1
    per_page = 20
    
    if (start_at > (per_page*int(total_git_referers/per_page))):
        start_at = per_page*int(total_git_referers/per_page)+1

    git_referers = GitReferers.objects(dependencies= name.replace("[dot]",".")).order_by("-stargazers_count").skip(start_at-1).limit(50)
    gs = GlobalStats.objects().first()
    
    return {"app": app, 
            "git_referers": git_referers, 
            "start_at": start_at,
            "end_at": min(start_at+per_page-1,total_git_referers),
            "per_page": per_page,
            "latest_git_update": time.strftime("%Y-%m-%d" , time.localtime(float(gs.last_git_project))),
            "app_count": total_git_referers,
            "visits": count_visits(request)}


@view_config(route_name="app_used_with",
             renderer='templates/app_used_with.jinja2',
             permission='view')
def view_app_used_with(request):
    name = request.matchdict["name"]
    app = Application.objects(title=name).first()
    return {"app": app, "visits": count_visits(request), "scimapID": cached_scimapID(request)}

@view_config(route_name="application",
             renderer='templates/application.jinja2',
             permission='view')
def view_application(request):
    name = request.matchdict["name"]
    app = Application.objects(title=name).first()
    global_stats = GlobalStats.objects().first()
    return {"app": app, "visits": count_visits(request), "global_stats": global_stats}


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

def splitEmpty(listing):
    splitlist = listing.split(",")
    if '' in splitlist: splitlist.remove('')
    return splitlist

allapps = []
allviews = []
lastappcheck = 0
secondsPerDay = 24*3600

def recalcAppList():
    """Requery a list of apps and views if it has not been queried in the last calendar day"""
    global lastappcheck, allviews, allapps, secondsPerDay
    if time.time() // secondsPerDay > lastappcheck // secondsPerDay:
        allapps = [app.title for app in Application.objects().order_by("title")]    
        allviews = [view.viewname for view in Views.objects()]
        lastappcheck = time.time()

@view_config(route_name="browse",
             renderer='templates/browse.jinja2',
             permission='view')
def view_explore(request):
    queries = dict()
    recalcAppList()
    order = request.params.get("order", "usage")
    
    if order=="-title": order = "title"
    
    queryname_raw = request.params.get("query-name", "").replace(" ","")
    queryname = splitEmpty(queryname_raw)
    if queryname != []: 
        queries["title__in"] = queryname
        
    queryview_raw = request.params.get("query-view", "").replace(" ","")
    queryview = splitEmpty(queryview_raw)
    if queryview != []: 
        queries["views__in"] = queryview
        
    relevantAppCount = Application.objects(**queries).count()
    
    try:
       start_at = int(request.params.get("start-at"))
    except:
       start_at = 1
    if (start_at < 1): start_at = 1
    per_page = 20
    
    if (start_at > (per_page*int(relevantAppCount/per_page))):
        start_at = per_page*int(relevantAppCount/per_page)+1
    
    apps = Application.objects(**queries).order_by(order).skip(start_at-1).limit(per_page)
    
    global_stats = GlobalStats.objects().first()
    return {"apps": apps, 
            "visits": count_visits(request), 
            "global_stats": global_stats,
            "queryname": queryname_raw, 
            "queryview": queryview_raw, 
            "allviews": allviews, 
            "allnames": allapps,
            "start_at": start_at, 
            "end_at":  min(relevantAppCount, start_at + per_page - 1),
            "per_page": per_page, 
            "app_count": relevantAppCount }
