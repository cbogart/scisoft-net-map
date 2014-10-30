from pyramid.config import Configurator
from mongoengine import connect, register_connection
from pyramid.security import Authenticated, remember, forget
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.events import BeforeRender

class SNMAuthorizationPolicy(object):
    def permits(self, context, principals,
                permission):
        return Authenticated in principals

def main(global_config, **settings):

    """ This function returns a Pyramid WSGI application.
    """
#    authn_policy = AuthTktAuthenticationPolicy(
#        'gabbleblotchits')
#    authz_policy = SNMAuthorizationPolicy()
    config = Configurator(
#        authentication_policy=authn_policy,
#        authorization_policy=authz_policy,
        settings=settings
        )

    config.include("pyramid_jinja2")
    config.include("pyramid_persona")

    def addSettings(event):
        event["sci_platform"] = settings["sci_platform"]
        event["google_tracking_code"] = settings["google_tracking_code"]

    config.add_subscriber(addSettings, BeforeRender)

    # Configuring static assets
    config.add_static_view(name="static", path="static")

    config.add_settings({"sci_platform": settings["sci_platform"],
                         "google_tracking_code": settings["google_tracking_code"]})
    config.add_route("home", "/")
    config.add_route("dsm", "/dsm")

    config.add_route("app_used_with",   "/application/{name}/used_with")
    config.add_route("app_usage",       "/application/{name}/usage")
    config.add_route("app_users",       "/application/{name}/users")
    config.add_route("application",     "/application/{name}")
    config.add_route("app_pubs", "/application/{name}/publications")

    config.add_route("compare", "/compare")
    config.add_route("about", "/about")
    config.add_route("data_source", "/data_source")
    config.add_route("browse", "/browse")
    config.add_route("overview", "/overview")
    #config.add_route("login", "/login")
    config.add_route("notebook", "/notebook")
    config.add_route("accept_login", "/accept_login")

    config.add_route("api_home", "/api")
    config.add_route("api_home.category", "/api/{category}")
    config.add_route("api_home.category.id", "/api/{category}/{id}")

    connect(settings['db_name'])
    register_connection('raw-records', settings['raw_db_name'])

    config.scan()
    return config.make_wsgi_app()
