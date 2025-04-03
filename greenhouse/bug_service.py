# bug_service.py

from flask import Flask, request, jsonify
import random
import requests
import threading
import time
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bugsarebad1234'

SERVICES = [
    'http://user_service:5001',
    'http://plant_service:5002',
    'http://simulation_service:5003',
    'http://websocket_service:5004'
]

bug_mode = False

def bug_mode_worker():
    while True:
        if bug_mode:
            service_url = random.choice(SERVICES)
            try:
                response = requests.get(f'{service_url}/trigger_bug')
                if response.status_code == 200:
                    logging.info(f"Bug triggered in {service_url}")
                else:
                    logging.error(f"Failed to trigger bug in {service_url}")
            except Exception as e:
                logging.error(f"Error triggering bug in {service_url}: {str(e)}")
        time.sleep(10)  # Trigger a bug every 10 seconds

@app.route('/toggle_bug_mode', methods=['POST'])
def toggle_bug_mode():
    global bug_mode
    bug_mode = not bug_mode
    logging.info(f"Bug mode toggled: {bug_mode}")
    return jsonify({"message": "Bug mode toggled", "bug_mode": bug_mode}), 200


@app.route('/bug_mode_status', methods=['GET'])
def bug_mode_status():
    return jsonify({"bug_mode": bug_mode}), 200

if __name__ == '__main__':
    threading.Thread(target=bug_mode_worker, daemon=True).start()
    app.run(host="0.0.0.0", port=5010)
