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

app = Flask(__name__)

BASE_PATH = os.path.abspath('.')
event_handlers = {}


def handle_event(event_type):
    def decorated_f(f):
        event_handlers[event_type] = f
        return f
    return decorated_f


@handle_event('cell_execute')
def execute_test(event):
    event_payload = event['payload']
    if not all([key in event_payload for key in ['username', 'notebook_key', 'question_key', 'code', 'output']]):
        return {'status': 'not-ok'}
    file_path = os.path.abspath(os.path.join(BASE_PATH, event_payload['notebook_key'], event_payload['question_key']))
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
    # FIXME: Use something less lame than O_APPEND
    with open('events', 'a') as f:
        f.write(json.dumps(event) + '\n')


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


@app.route('/receive/<string:event_type>', methods=['POST'])
def receive(event_type):
    event_payload = request.get_json(force=True)
    event = make_event(event_type, event_payload)
    return json.dumps(dispatch_event(event))

if __name__ == '__main__':
    app.run(debug=True)
