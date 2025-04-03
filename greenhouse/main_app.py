# main_app.py

from flask import Flask, render_template, session, redirect, url_for, request, jsonify
import requests
import logging


app = Flask(__name__)
app.config['SECRET_KEY'] = 'plantsarecool1234'

USER_SERVICE_URL = 'http://user_service:5001'
PLANT_SERVICE_URL = 'http://plant_service:5002'
SIMULATION_SERVICE_URL = 'http://simulation_service:5003'
WEBSOCKET_SERVICE_URL = 'http://websocket_service:5004'
BUG_SERVICE_URL = 'http://bug_service:5010'

@app.route('/')
def index():
    logging.info("Rendering index page...")
    return render_template('index.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user_id' not in session:
        logging.error("Unauthorized access to dashboard")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Fetch user data
    user_response = requests.get(f'{USER_SERVICE_URL}/user/{user_id}')
    if user_response.status_code != 200:
        logging.error("Failed to fetch user data")
        return "Failed to fetch user data", 500
    user = user_response.json()
    
    # Fetch plants data
    plant_response = requests.get(f'{PLANT_SERVICE_URL}/plants/{user_id}')
    if plant_response.status_code != 200:
        logging.error("Failed to fetch plants data")
        return "Failed to fetch plants data", 500
    plants = plant_response.json()
    
    # Start simulation for this user
    simulation_response = requests.post(f'{SIMULATION_SERVICE_URL}/start_simulation', json={'user_id': user_id})
    if simulation_response.status_code != 200:
        logging.error("Failed to start simulation")
        return "Failed to start simulation", 500
    
    return render_template('dashboard.html', user=user, plants=plants)

@app.route('/toggle_error_mode', methods=['POST'])
def toggle_error_mode():
    # Toggle bug mode in the bug service
    response = requests.post(f'{BUG_SERVICE_URL}/toggle_bug_mode')
    if response.status_code == 200:
        logging.info("Toggled error mode")
        return redirect(request.referrer or url_for('index'))
    else:
        logging.error("Failed to toggle error mode")
        return "Failed to toggle bug mode", 500

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        response = requests.post(f'{USER_SERVICE_URL}/signup', data=request.form)
        if response.status_code == 200:
            return redirect(url_for('login'))
        return response.text
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        response = requests.post(f'{USER_SERVICE_URL}/login', data=request.form)
        if response.status_code == 200:
            logging.info(f"User {response.json().get('user_id')} logged in")
            session['user_id'] = response.json().get('user_id')
            return redirect(url_for('dashboard'))
        return response.text
    return render_template('login.html')

@app.route('/logout')
def logout():
    response = requests.get(f'{USER_SERVICE_URL}/logout')
    if response.status_code == 200:
        logging.info("User logged out")
        session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/bug_mode_status', methods=['GET'])
def bug_mode_status():
    # Toggle bug mode in the bug service
    response = requests.get(f'{BUG_SERVICE_URL}/bug_mode_status')
    logging.info(response.json())
    if response.status_code == 200:
        logging.info("Toggled error mode")
        return jsonify(response.json())
    else:
        logging.error("Failed to toggle error mode")
        return "Failed to toggle bug mode", 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
