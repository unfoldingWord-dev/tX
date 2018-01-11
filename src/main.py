"""The Translation Converter Service (tx) provides various RESTfull commands for manipulating content from the Door43 Content Services.

"""

from flask import request, url_for
from flask_api import FlaskAPI, status, exceptions
from service_manager import ServiceManager
from services.sample import sample_service

app = FlaskAPI(__name__)
# use api to add routes so we can automate some things
api = ServiceManager(app)

notes = {
    0: 'do the shopping',
    1: 'build the codez',
    2: 'paint the door',
}

routes = []

def note_repr(key):
    return {
        'url': request.host_url.rstrip('/') + url_for('notes_detail', key=key),
        'text': notes[key]
    }


@api.route('/')
def index():
    """
    Displays a list of registered services

    """
    return api.formatted_routes(request.host_url)

@api.register_route(sample_service, '/sample')
@api.register_route(sample_service, '/sample/<string:name>')

@api.route("/list", methods=['GET', 'POST'])

def notes_list():
    """
    List or create notes.
    """
    if request.method == 'POST':
        note = str(request.data.get('text', ''))
        idx = max(notes.keys()) + 1
        notes[idx] = note
        return note_repr(idx), status.HTTP_201_CREATED

    # request.method == 'GET'
    return [note_repr(idx) for idx in sorted(notes.keys())]


@api.route("/<int:key>/", methods=['GET', 'PUT', 'DELETE'])
def notes_detail(key):
    """
    Retrieve, update or delete note instances.
    """
    if request.method == 'PUT':
        note = str(request.data.get('text', ''))
        notes[key] = note
        return note_repr(key)

    elif request.method == 'DELETE':
        notes.pop(key, None)
        return '', status.HTTP_204_NO_CONTENT

    # request.method == 'GET'
    if key not in notes:
        raise exceptions.NotFound()
    return note_repr(key)


@app.errorhandler(404)
def page_not_found(e):
    return e

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
