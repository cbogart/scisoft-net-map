import os
import json
import sys
import pdb
from db_objects import *
from pymongo import Connection, MongoClient

from pyramid.view import (
    view_config,
    view_defaults
)

class LimitedDict:
    def __init__(self, size):
        self.size = size
        self.content = {}
        self.keys = []
        
    def __getitem__(self, index):
        return self.content[index]
        
    def get(self, index, default):
        return self.content.get(index, default)
        
    def __setitem__(self, index, value):
        if index in self.content:
            self.content[index] = value
            self.keys.remove(index)
            self.keys.append(index)
            return
        if len(self.keys) > self.size:
            del self.content[self.keys[0]]
            self.keys = self.keys[1:]            
        self.keys.append(index)
        self.content[index] = value
        
    def memoize(self, index, fn, fnargs):
        if index not in self.content: 
            self[index] = fn(**fnargs)
        return self[index]

memoCache = LimitedDict(10)


"""
All API calls have the following structure:
/api/:category/:id

For example: /api/apps/MyApp

In order to add new category just add new method in ApiViews class.
Both def apps(), def stat() can be used as reference point

For a given category nested functions are defined in order to address
different calls within category.
For example: /api/stat/usage_over_time is defined as
def usage_over_time() under def stat()

In order to add new type of data you can simply define new nested function
and process user request in it.
"""
@view_defaults(renderer="json")
class ApiViews:
    def __init__(self, request):
        self.request = request
        self.TEMPLATE = {"version": 0.1,
                         "status": None,
                         "data": None}
        self.STATUS_OK = "OK"
        self.STATUS_ERROR = "ERROR"

    @view_config(route_name="api_home",
                 permission="api")
    @view_config(route_name="api_home.category",
                 permission="api")
    @view_config(route_name="api_home.category.id",
                 permission="api")
    def home(self):
        request = self.request
        response = self.TEMPLATE.copy()
        matchdict = request.matchdict
        category = matchdict.get("category")

        if category is None:
            response["status"] = self.STATUS_OK
            response["data"] = repr(request)
            return response

        try:  # TODO: Handle non existing path
            _id = matchdict.get("id")
            response["data"] = getattr(self, category)(request, _id)
            response["status"] = self.STATUS_OK
        except Exception, e:
            response["status"] = self.STATUS_ERROR
            response["data"] = str(e)

        return response

    #def register(self, request, type):
        #""" Register a user's use of an application,
        #dropping the information into a mongo collection.
        #Parameters are ignored.
        #"""
        #c = Connection()
        #rawrecords = c["snm-raw-records"]
        #record = json.loads(request.body)
        #rawrecords["lariat"].save(record)
        #return "Registered"

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
                print "Irrelevantly, Linking ", request.route_url('application', name=app.title)
                result.append({
                    "id": str(app.id),
                    "name": app.title.replace("[dot]","."),
                    "link": request.route_url('application', name=app.title)
                })
            return result

        return list(**request.params)

    def stat(self, request, type):
        """ Return list of data sources available
        or find specific one "api/stat/:some_stat"
        """
        def data_over_time(group_by, id, stat_type):
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
            stat_object = globals()[stat_type]
            for entry in stat_object.objects(application__in=id.split(",")).all():
                result.append({"data": entry.to_mongo()[group],
                               "title": entry.application.title.replace("[dot]",".")})
            return result

        def version_data_over_time(group_by, id, stat_type):
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
            stat_object = globals()[stat_type]
            for entry in sorted(stat_object.objects(application__in=id.split(",")).all(), key=lambda o: o.version):
                result.append({"data": entry.to_mongo()[group],
                               "version": entry.version,
                               "title": entry.application.title.replace("[dot]",".")})
            return result
        
        def system_data_over_time(group_by, category, stat_type):
            d = {"day": "daily",
                 "week": "weekly",
                 "month": "monthly"}
            group = d.get(group_by)
            if group is None:
                raise Exception("Group_by argument "
                                "should be one of {}".format(
                                    ",".join(d.keys())))

            if category is None:
                category = "R sessions"
                #raise Exception("Please specify category id")

            result = []
            stat_object = globals()[stat_type]
            for entry in stat_object.objects(category__in=category.split(",")).all():
                result.append({"data": entry.to_mongo()[group],
                               "title": category})
            return result

        def user_vector(id):
           result = dict()
           maxuse = 0
           for entry in RawRecords.objects(user=id).all():
               for pkg in entry.pkgT:
                   pkgname = pkg.replace("[dot]", ".").split("/")[0]
                   result[pkgname] = result.get(pkgname, 0) + 1
                   if (result[pkgname] > maxuse): maxuse = result[pkgname]
                   for dep in entry.pkgT[pkg] if not (isinstance(entry.pkgT[pkg], str)) else [entry.pkgT[pkg]]:
                       dep1 = dep.replace("[dot]", ".").split("/")[0]
                       result[dep1] = result.get(dep1, 0) + 1
                       if (result[dep1] > maxuse): maxuse = result[dep1]
           if (maxuse > 0):
               for pkg in result: result[pkg] = result[pkg]*1.0/maxuse
           return result

        def raw_user(id):
           result = []
           for entry in RawRecords.objects(user=id).all():
                try:
                    result.append({
                      "user": entry.user,
                      "pkgT": { k.replace("[dot]","."): entry.pkgT[k] for k in entry.pkgT },
                      "jobID": entry.jobID,
                      "startTime": entry.startTime,
                      "startEpoch": entry.startEpoch,
                      "endTime": entry.endTime,
                      "endEpoch": entry.endEpoch,
                      "platform": entry.platform,
                      "userMetadata": entry.userMetadata,
                    })
                except Exception, e:
                    print "ERROR: ", str(e), str(entry)
           return result
                               
        def usage_over_time(group_by="day", id=None):
           return data_over_time(group_by, id, "Usage")
           
        def version_usage_over_time(group_by="day", id=None):
           return version_data_over_time(group_by, id, "VersionUsage")
           
        def version_users_over_time(group_by="day", id=None):
           return version_data_over_time(group_by, id, "VersionUsersUsage")
           
        def system_usage(group_by="day", id=None):
           print "system_usage:", group_by, id
           return system_data_over_time(group_by, id, "SystemUsage")
           
        def system_users(group_by="day", id=None):
           print "system_users:", group_by, id
           return system_data_over_time(group_by, id, "SystemUsersUsage")
           
        def git_usage_over_time(group_by="day", id=None):
           return data_over_time(group_by, id, "GitUsage")

        def users_over_time(group_by="day", id=None):
            return data_over_time(group_by, id, "UsersUsage")
        
        def overall_stats():
            gs = GlobalStats.objects().first()
            return {
                "git_projects": gs.num_git_projects_scraped,
                "r_sessions": RawRecords.objects().count(),
                #"r_users": 6,
                "repositories": Application.objects().item_frequencies('repository'),                          
                #"earliest_git_update": "Mon Mar 23 2015",
                #"earliest_r_update": RawRecords.objects().first()["receivedEpoch"],
                "latest_git_update": gs.last_git_project,
                "latest_r_packet": gs.last_r_packet
                    }

        def dictsum(d1, d2):
            for k in d2:
                d1[k] = d1.get(k,0) + d2[k]

        def git_force_directed(id=None, clustered=False, limit=9999):
            return force_directed_helper(id,clustered,limit,datasource=GitCoOccurenceLinks,relevantUsage = lambda app: app.git_usage)
            
        def force_directed(id=None, clustered=False, limit=9999):
            return force_directed_helper(id,clustered,limit,datasource=CoOccurenceLinks,relevantUsage = lambda app: app.usage)
            
        def force_directed_helper(id=None, clustered=False, limit=9999, datasource=CoOccurenceLinks,relevantUsage = lambda app: app.usage):
            from bson.objectid import ObjectId
            app = Application.objects.get(id=id)

            #pdb.set_trace()
            mainlinks = list(datasource.objects(focal= app.id).limit(int(limit)+1))
            threshhold = mainlinks[-1]["scaled_count"]
            neighbors = [link["other"] for link in mainlinks]
            neighbor_ids = [link["other"].id for link in mainlinks]
            sidelinks = datasource.objects(__raw__ = \
                  {"focal": { "$in": neighbor_ids },
                   "other": { "$in": neighbor_ids+[app.id]}})
            sidelinks = list(sidelinks)
            
            alll = mainlinks + sidelinks
            links = [{"source": l["focal"].id.__str__(),
                      "target": l["other"].id.__str__(),
                      "type": l["type"],
                      "raw": l["raw_count"],
                      "scaled": l["scaled_count"]} for l in alll]
            
            apps = Application.objects(__raw__={ "_id": { "$in": neighbor_ids + [app.id] } } )
            nodes = [{"name": app.title.replace("[dot]","."),
                      "id": app.id.__str__(),
                      "uses": relevantUsage(app),
                      "publications": app.publications,
                      "link": request.route_url('app_used_with', name=app.title)
                     } for app in apps]
            
            return {"nodes": nodes, "links": links}

        def unknown_stat(*args, **kwargs):
            raise Exception("Unknown request type")

        if type is None:
            return [{"id": "usage_over_time"},
                    {"id": "users_over_time"},
                    {"id": "system_users"},
                    {"id": "system_usage"},
                    {"id": "overall_stats"},
                    {"id": "force_directed"},
                    {"id": "git_force_directed"}]

        #  locals().get(type, unknown_stat)(**request.params)
        return memoCache.memoize(type + str(request.params), 
               locals().get(type, unknown_stat), request.params)

