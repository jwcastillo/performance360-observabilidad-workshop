# websocket_service.py

from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] = 'plantsarecool1234'
socketio = SocketIO(app, cors_allowed_origins="*", engineio_logger=True)

PLANT_SERVICE_URL = 'http://plant_service:5002'

active_users = {}
BUGS = False

@app.route('/trigger_bug', methods=['GET'])
def bug():
    logging.error("Triggering bug...")
    global BUGS
    BUGS = True
    return "Bug triggered", 200

@socketio.on('connect')
def handle_connect():
    user_id = request.args.get('user_id')  # Get user_id from query parameters
    if user_id:
        active_users[user_id] = {
            'error_mode': False  # You can set the error_mode based on your application logic
        }
        join_room(str(user_id))
        logging.info(f"User {user_id} connected and joined their room with error mode {active_users[user_id]['error_mode']}.")

@socketio.on('disconnect')
def on_disconnect():
    user_id = request.args.get('user_id')
    if user_id in active_users:
        del active_users[user_id]
        leave_room(str(user_id))
        logging.info(f"User {user_id} disconnected and was removed from active list.")

@socketio.on('add_plant')
def handle_add_plant(data):
    global BUGS
    if BUGS == True:
        logging.error("What a nasty bug! It flew into the websocket service and stopped the request to add plant.")
        BUGS = False
        return "Failed to add plant"
    
    user_id = request.args.get('user_id')
    if not user_id or user_id not in active_users:
        emit('error', {'error': 'Unauthorized or failed attempt to add plant'})
        return
    
    plant_name = data.get('plant_name')
    plant_type = data.get('plant_type')

    response = requests.post(f'{PLANT_SERVICE_URL}/plants', json={
        'plant_name': plant_name,
        'plant_type': plant_type,
        'user_id': user_id
    })

    if response.status_code == 201:
        plant_data = response.json()
        emit('new_plant', {
            'plant_id': plant_data['plant_id'],
            'plant_name': plant_name,
            'plant_type': plant_type
        }, room=str(user_id))
        logging.info(f"New plant {plant_name} added successfully for user {user_id}.")
    else:
        emit('error', {'error': 'Failed to add plant'})
        logging.error(f"Failed to add plant {plant_name} for user {user_id}.")

if __name__ == '__main__':
    socketio.run(app=app, host="0.0.0.0", port=5004, allow_unsafe_werkzeug=True)
