# simulation_service.py

from flask import Flask, request
from random import randint, uniform
import logging
from flask_socketio import SocketIO, emit, join_room, leave_room
import requests
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'plantsarecool1234'
socketio = SocketIO(app, cors_allowed_origins="*", engineio_logger=True)

BUGS = False

PLANT_SERVICE_URL = 'http://plant_service:5002'

active_users = {}
simulation_threads = {}
stop_flags = {}

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    data = request.json
    user_id = data.get('user_id')
    if user_id:
        if user_id in simulation_threads:
            stop_flags[user_id] = True
            simulation_threads[user_id].join()  # Wait for the old thread to finish
        stop_flags[user_id] = False
        thread = threading.Thread(target=simulate_plant_data, args=(user_id,))
        simulation_threads[user_id] = thread
        thread.start()
        logging.info(f"Simulation started for user {user_id}.")
        return "Simulation started", 200
    return "Invalid user_id", 400

@app.route('/trigger_bug', methods=['GET'])
def bug():
    logging.error("Triggering bug...")
    global BUGS
    BUGS = True
    return "Bug triggered", 200

@socketio.on('connect')
def handle_connect():
    user_id = request.args.get('user_id')
    if user_id:
        active_users[user_id] = True
        join_room(str(user_id))
        logging.info(f"User {user_id} connected and joined room.")

@socketio.on('disconnect')
def on_disconnect():
    user_id = request.args.get('user_id')
    if user_id in active_users:
        del active_users[user_id]
        leave_room(str(user_id))
        logging.info(f"User {user_id} disconnected and left room.")
        if user_id in stop_flags:
            stop_flags[user_id] = True
            if user_id in simulation_threads:
                simulation_threads[user_id].join()

def simulate_plant_data(user_id):
    while not stop_flags[user_id]:
        socketio.sleep(2)
        try:
            response = requests.get(f'{PLANT_SERVICE_URL}/plants/{user_id}')
            if response.status_code == 200:
                plants = response.json()
                for plant in plants:
                    fake_data = {
                        'temperature': round(uniform(20.0, 30.0), 2),
                        'humidity': round(uniform(40.0, 60.0), 2),
                        'water_level': randint(1, 10),
                        'number_of_insects': randint(0, 10)
                    }
                    global BUGS
                    if BUGS == True:
                            logging.error("What a nasty bug! It flew into the simulation service and stopped producing sensor readings.")
                            BUGS = False
                    else:
                        socketio.emit('update_plant', {'plant_id': plant['id'], 'data': fake_data}, room=str(user_id))
                        logging.debug(f"Simulated data for plant {plant['id']} sent to user {user_id}")
            else:
                logging.error(f"Failed to fetch plants for user {user_id}. Status code: {response.status_code}")
        except Exception as e:
            logging.error(f"Error in simulation thread for user {user_id}: {str(e)}")

if __name__ == '__main__':
    socketio.run(app=app, host="0.0.0.0", port=5003, allow_unsafe_werkzeug=True)
