from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')

    # Configuring static assets
    config.add_static_view(name='static', path='static')

    config.add_route('home', '/')
    config.add_route('overview', '/overview')

    config.scan()
    return config.make_wsgi_app()
