"""
This is a more complex illustration of a sample service.
"""

from flask import request, url_for
from flask_api import status, exceptions

notes = {
    0: 'do the shopping',
    1: 'build the codez',
    2: 'paint the door',
}

def note_repr(key):
    """
    Prepares the note response

    :param key: The note key
    :type key: int
    :return: The formatted note response
    """
    return {
        'url': request.host_url.rstrip('/') + url_for('notes_detail', key=key),
        'text': notes[key]
    }

def notes_list():
    """
    Lists the notes

    :return: A list of note objects
    """
    if request.method == 'POST':
        note = str(request.data.get('text', ''))
        idx = max(notes.keys()) + 1
        notes[idx] = note
        return note_repr(idx), status.HTTP_201_CREATED

    # request.method === 'GET'
    return [note_repr(idx) for idx in sorted(notes.keys())]

def notes_detail(key):
    """
    Retrieve, update or delete note instances.

    :param key: The note key
    :type key: int
    :return:
            When PUTing a new note this will return the note object.
            When DELETEing a note this will return an empty body with a 204 header
            When GETing a note this will return the note object
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