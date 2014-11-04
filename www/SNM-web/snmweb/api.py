import os
import json
import sys
from db_objects import *
from pymongo import Connection
from tarjan import clusteringOrder

from pyramid.view import (
    view_config,
    view_defaults
)

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
                               "title": entry.application.title})
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


        def users_over_time(group_by="day", id=None):
            return data_over_time(group_by, id, "UsersUsage")


        #
        #  N.B. the "co_uses" element is not a simple count; it's a little
        #   dict with 2 keys: "static" and "logical", with separate counts
        #   for both kinds of usage.  The effective "value" of this element
        #   is the static count, UNLESS the count is zero, in which case the
        #   logical count.
        #
        def force_directed(id=None, clustered=False):
            nodes = []
            links = []

            max_co_uses = GlobalStats.objects()[0].max_co_uses

            def normalizeValue(coUses, targetUsage):
                normalized = { k : int(0 if (coUses[k] == 0) else
                                   coUses[k]*10/targetUsage) 
                         for k in coUses }
                return normalized
            
            def oldNormalizeValue(coUses):
                return { k : (0 if (coUses[k] == 0) else
                                   1+coUses[k]*9/max(coUses[k], max_co_uses[k], 1)) 
                         for k in coUses }
            
            def hasLink(coUses):
                return (coUses["static"]  > 0 or
                        coUses["logical"] > 0)

            if id is None:
                nodedict = {}
                cooc = CoOccurence.objects()
                for c in cooc:
                    app_id = c.application.id.__str__()
                    nodedict[app_id] = {"name": c.application.title,
                                  "id": app_id,
                                  "publications": c.application.publications,
                                  "link": request.route_url('application', name=c.application.title)}
                    for l in c.links:
                        nodedict[l.app.id.__str__()] = {"name": l.app.title,
                                      "id": l.app.id.__str__(),
                                      "publications": l.app.publications,
                                      "link": request.route_url('application', name=l.app.title)}
                    for l in c.links:
                        if hasLink(l.co_uses):
                            links.append({
                                "source": app_id,
                                "target": l.app.id.__str__(),
                                "value":  normalizeValue(l.co_uses, c.application.usage) #l.app.usage)
                            })
                nodes = nodedict.values()
            else:
                from bson.objectid import ObjectId
                app = Application.objects.get(id=id)
                nodelist = [ObjectId(id)]
                fromcooc = CoOccurence.objects(__raw__= { "links": { "$elemMatch": { "app": ObjectId(id) } } })
                nodelist = nodelist + [fc.application.id for fc in fromcooc]
                tocooc = CoOccurence.objects(__raw__= { "application": ObjectId(id)} )
                for tc in tocooc:
                    nodelist = nodelist + [tcl.app.id for tcl in tc.links]
                edgecooc = CoOccurence.objects(__raw__= { "application": { "$in" : nodelist }, "links": { "$elemMatch": { "app": { "$in" : nodelist } } }})
                for fan in edgecooc:
                    src = fan.application
                    for destinf in fan.links:
                        dest = destinf.app.id
                        if (dest in nodelist):
                            if (hasLink(destinf.co_uses)):
                                links.append({"source": src.id.__str__(),
                                             "target": dest.__str__(),
                                             "value": normalizeValue(destinf.co_uses, app.usage)
				})    #destinf.app.usage)})

                for c in Application.objects(__raw__={ "_id": { "$in": nodelist } } ):
                    app_id = c.id.__str__()
                    nodes.append({"name": c.title,
                                  "id": app_id,
                                  "publications": c.publications,
                                  "link": request.route_url('application', name=c.title)})

            if (clustered):
                nodes = clusteringOrder(nodes, links)

            return {"nodes": nodes, "links": links}

        def unknown_stat(*args, **kwargs):
            raise Exception("Unknown request type")

        if type is None:
            return [{"id": "usage_over_time"},
                    {"id": "users_over_time"},
                    {"id": "force_directed"}]

        return locals().get(type, unknown_stat)(**request.params)

