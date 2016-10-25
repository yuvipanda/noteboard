"""
Simple event server for Tuesday's THW

This is simplistic event bus setup for doing serverside notebook answer checks
for Tuesday's The Hacker Within Python Olympics.
"""
import os
import json
import time
import uuid

from flask import Flask, request
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
# Insecure! Let's not do this forever :D
cors = CORS(app)

BASE_PATH = os.path.abspath('.')
event_handlers = {}

client = MongoClient('localhost', 27017, connect=False)


def handle_event(event_type):
    def decorated_f(f):
        event_handlers[event_type] = f
        return f
    return decorated_f


@handle_event('notebook_opened')
def notebook_started(event):
    event_payload = event['payload']
    query = {
        'username': event_payload['username'],
        'notebook_key': event_payload['notebook_key']
    }
    if not client.thw.notebook_starts.find_one(query):
        # First time notebook opening!
        data = query.copy()
        data['started_at'] = event['timestamp']
        data['event'] = event
        client.thw.notebook_starts.insert_one(data)


@handle_event('correct_answer')
def correct_answer(event):
    event_payload = event['payload']['original']['payload']
    notebook_query = {
        'username': event_payload['username'],
        'notebook_key': event_payload['notebook_key']
    }
    notebook_started = client.thw.notebook_starts.find_one(notebook_query)
    answer_query = {
        'username': event_payload['username'],
        'notebook_key': event_payload['notebook_key'],
        'answer_key': event_payload['answer_key'],
    }
    if not client.thw.answers.find_one(answer_query):
        data = answer_query.copy()
        data.update({
            'event': event,
            'time_from_start': event['timestamp'] - notebook_started['started_at']
        })
        client.thw.answers.insert_one(data)

@handle_event('cell_execute')
def execute_test(event):
    event_payload = event['payload']
    if not all([key in event_payload for key in ['username', 'notebook_key', 'answer_key', 'code', 'output']]):
        return {'status': 'not-ok'}
    file_path = os.path.abspath(os.path.join(BASE_PATH, event_payload['notebook_key'], event_payload['answer_key']))
    if not file_path.startswith(BASE_PATH):
        # Directory traversal attack!
        # FIXME: Make these statuses actually understandable!
        return {'status': 'invalid-keys'}
    if os.path.exists(file_path):
        with open(file_path) as f:
            answer = f.read().strip()
        if answer == event_payload['output'].strip():
            # Don't return this - only return correct
            # FIXME: wtf do we do with this? In process event listeners ugh
            dispatch_event(make_event('correct_answer', {'original': event}))
            return {'status': 'correct'}
    return {'status': 'incorrect'}


def write_event(event):
    """
    Writes the event out to a file, as atomically as possible.
    """
    print(repr(event))
    # OMG, pymongo modifies the data you pass it! WTF PYMONGO
    # Shallow copy is ok, since pymongo doesn't reach into objects and change
    # them
    client.thw.events.insert_one(event.copy())


def make_event(event_type, event_payload):
    return {
        "timestamp": time.time(),
        "type": event_type,
        "payload": event_payload,
        "id": str(uuid.uuid4())
    }


def dispatch_event(event):
    event_type = event['type']
    write_event(event)
    if event_type in event_handlers:
        return event_handlers[event_type](event)
    return {}


@app.route('/receive/<string:event_type>', methods=['POST'])
def receive(event_type):
    event_payload = request.get_json(force=True)
    event = make_event(event_type, event_payload)
    ret = {
        'response': dispatch_event(event),
        'event': event
    }
    print(repr(ret))
    return json.dumps(ret)

if __name__ == '__main__':
    app.run(debug=True)
