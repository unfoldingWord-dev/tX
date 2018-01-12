"""
This module bootstraps the API setup and registers all of the available services.
"""

from flask import request
from flask_api import FlaskAPI
from service_manager import ServiceManager
from services.sample import sample_service
from src.services.notes.notes import notes_list, notes_detail

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
    """
    api.register_route(sample_service, '/sample')
    api.register_route(sample_service, '/sample/<string:name>')
    api.register_route(notes_list, '/list', methods=['GET', 'POST'])
    api.register_route(notes_detail, '/<int:key>/', methods=['GET', 'PUT', 'DELETE'])

if __name__ == "__main__":
    register_services(api)
    app.run(debug=True, threaded=True)
