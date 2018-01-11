import re
from flask_api import FlaskAPI

class ServiceManager():
    """
    The ServiceManager is a light wrapper around FlaskAPI
    that allows us to perform additional processing when routes are registered.
    """

    def __init__(self, app):
        """
        :param app: The global FlaskAPI instance
        :type app: FlaskAPI
        """
        self.__routes = {}
        self.__app = app

    def register_route(self, func, rule, **options):
        """Like :meth:`Flask.route` but with additional processing.
        The route is stored in a list so we can keep track of all the exposed API endpoints.

        :param func: The function that will be executed for the URL rule.
        :type func: basestring
        :param rule: The URL rule to match in order to execute the endpoint.
        :type rule: basestring
        :param endpoint: The name of the exposed endpoint. Flask
                         itself assumes the name of the view function as
                         the endpoint.
        :type endpoint: basestring

        :return: The registered function.
        """
        doc = ""
        if func.__doc__:
            doc = re.sub(r'\s+', ' ', func.__doc__.strip())
        self.__routes[func.__name__] = {
            'rule': rule,
            'doc': doc
        }
        endpoint = options.pop('endpoint', None)
        self.__app.add_url_rule(rule, endpoint, func, **options)
        return func

    def route(self, rule, **options):
        """A decorator version of :meth:`register_route`.
        This allows you to use the decorator syntax like:

        >>> @api.route('/')
        >>> def index():

        :param rule: The URL rule to match in order to execute the endpoint.
        :type rule: basestring
        :param endpoint: The name of the exposed endpoint. Flask
                         itself assumes the name of the view function as
                         the endpoint.
        :type endpoint: basestring
        """
        def decorator(f):
            return self.register_route(f, rule, **options)

        return decorator

    def formatted_routes(self, host_url):
        """
        Returns a dictionary of endpoints that have been registered with the api.
        This is useful for displaying a summary of available endpoints.

        :param host_url: The host address e.g. https://example.com
        :type host_url: basestring

        :return:
            A dict mapping endpoints to their corresponding route and summary.
            For example:

            >>> {
            >>>     'my_service': {
            >>>         'route': 'https://example.com/myservice/<string:some_arg>',
            >>>         'doc': 'This is my function. It takes one argument.'
            >>>     }
            >>> }
        """
        routes = {}
        for key, value in self.__routes.iteritems():
            url = host_url.rstrip('/') +  value['rule']
            routes[key] = {
                'route': url,
                'doc': value['doc']
            }
        return routes