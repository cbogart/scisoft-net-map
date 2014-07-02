from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')

    # Configuring static assets
    config.add_static_view(name='static', path='static')

    config.add_route('home', '/')
    config.add_route('app_details', '/app_details')
    config.add_route('application', '/application/{name}')
    config.add_route('compare', '/compare')
    config.add_route('data-sources', '/data-sources')
    config.add_route('browse', '/browse')
    config.add_route('overview', '/overview')
    config.add_route('api_home', '/api')
    config.add_route('api_home.category', '/api/{category}')
    config.add_route('api_home.category.id', '/api/{category}/{id}')

    config.scan()
    return config.make_wsgi_app()
