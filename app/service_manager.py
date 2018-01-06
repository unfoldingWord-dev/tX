from flask_api import FlaskAPI

class ServiceManager():

    def __init__(self, app):
        """
        :param app:
        :type app: FlaskAPI
        """
        self.__routes = {}
        self.__app = app

    def register_route(self, func, rule, **options):
        """Like :meth:`Flask.route` but with additional steps.
        The route is stored in a list so we can keep track of all the exposed API end points.
        :param self:
        :param rule: the URL rule as string
        :param endpoint: the endpoint for the registered URL rule. Flask
                         itself assumes the name of the view function as
                         endpoint
        :param options: the options to be forwarded to the underlying rule.
        """
        doc = ""
        if func.__doc__:
            doc = func.__doc__.strip()
        self.__routes[func.__name__] = {
            'rule': rule,
            'doc': doc
        }
        endpoint = options.pop('endpoint', None)
        self.__app.add_url_rule(rule, endpoint, func, **options)
        return func

    def route(self, rule, **options):
        """A decorator version of :meth:`Flask.route`
        :param self:
        :param rule: the URL rule as string
        :param endpoint: the endpoint for the registered URL rule. Flask
                         itself assumes the name of the view function as
                         endpoint
        :param options: the options to be forwarded to the underlying rule.
        """
        def decorator(f):
            return self.register_route(f, rule, **options)

        return decorator

    def routes(self):
        """
        Returns a list of routes that have been registered
        :return:
        """
        return self.__routes

    def formatted_routes(self, host_url):
        routes = {}
        for key, value in self.__routes.iteritems():
            url = host_url.rstrip('/') +  value['rule']
            routes[key] = {
                'route': url,
                'doc': value['doc']
            }
        return routes