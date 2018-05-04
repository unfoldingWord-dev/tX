"""
This module bootstraps the API setup and registers all of the available services.
"""

from flask import request
from flask_api import FlaskAPI
from service_manager import ServiceManager
from services.sample import sample_service
from services.client.client_webhook import ClientWebhookHandler
#from services.client.client_converter_callback import ClientConverterCallback
#from services.client.client_linter_callback import ClientLinterCallback
from services.converters.md2html_converter import Md2HtmlConverter
from services.converters.usfm2html_converter import Usfm2HtmlConverter

app = FlaskAPI(__name__)
api = ServiceManager(app)

@api.route('/')
def index():
    """
    Displays the available services.

    :return: A dictionary of registered endpoints.
    """
    return api.formatted_routes(request.host_url)

@app.errorhandler(404)
def page_not_found(e):
    """
    Handles 404 errors experienced by the clients.

    :param e: The exception object
    :return: The exception object
    """
    return e

def register_services(api):
    """
    Registers the available services with the
    Service Manager.
    New services should be registered inside this function.

    :param api: An instance of the Service Manager
    :type api: ServiceManager
    """
    api.register_route(sample_service, '/sample')
    api.register_route(sample_service, '/sample/<string:name>')
    # Client routes
    #api.register_route(, '/client/callback') # appears deprecated
    #api.register_route(ClientConverterCallback, '/client/callback/converter')
    #api.register_route(ClientConverterCallback, '/client/callback/converter', methods=['POST'])
    #api.register_route(ClientLinterCallback, '/client/callback/linter')
    #api.register_route(ClientLinterCallback, '/client/callback/linter', methods=['POST'])
    api.register_route(ClientWebhookHandler, '/client/webhook')
    api.register_route(ClientWebhookHandler, '/client/webhook', methods=['POST'])
    # tX routes
    #api.register_route(ClientWebhook, '/job')
    #api.register_route(ClientWebhook, '/job', methods=['GET', 'POST'])
    #api.register_route(ClientWebhook, '/job/<string:jobid>')
    #api.register_route(ClientWebhook, '/job/<string:jobid>', methods=['GET'])
    #api.register_route(ClientWebhook, '/module')
    #api.register_route(ClientWebhook, '/module', methods=['POST'])
    #api.register_route(ClientWebhook, '/print')
    #api.register_route(ClientWebhook, '/print', methods=['GET'])
    # tX Converter routes
    api.register_route(Md2HtmlConverter, '/converter/md2html')
    api.register_route(Md2HtmlConverter, '/converter/md2html', methods=['POST'])
    api.register_route(Usfm2HtmlConverter, '/converter/usfm2html')
    api.register_route(Usfm2HtmlConverter, '/converter/usfm2html', methods=['POST'])

if __name__ == "__main__":
    register_services(api)
    app.run(debug=True, threaded=True)
