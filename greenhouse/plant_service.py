# plant_service.py

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import logging
import requests


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db:5432/plant_service_db'
db = SQLAlchemy(app)

SIMULATION_SERVICE_URL = 'http://simulation_service:5003'
BUGS = False

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    plant_type = db.Column(db.String(50), nullable=False)
    health_data = db.Column(db.String(300), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

@app.route('/plants', methods=['POST'])
def add_plant():
    global BUGS
    if BUGS == True:
        logging.error("What a nasty bug! It flew into the plant service and stopped adding plants.")
        BUGS = False
        return "Failed to add plant", 500
    data = request.json
    new_plant = Plant(
        name=data['plant_name'],
        plant_type=data['plant_type'],
        health_data="Healthy",
        user_id=data['user_id']
    )
    db.session.add(new_plant)
    db.session.commit()
    logging.info(f"New plant {data['plant_name']} added successfully.")
        # Start simulation for this user
    simulation_response = requests.post(f'{SIMULATION_SERVICE_URL}/start_simulation', json={'user_id': data['user_id']})
    if simulation_response.status_code != 200:
        return "Failed to start simulation", 500
    
    return jsonify({'plant_id': new_plant.id}), 201

@app.route('/plants/<int:user_id>', methods=['GET'])
def get_plants(user_id):
    global BUGS
    if BUGS == True:
        logging.error("What a nasty bug! It flew into the plant service and stopped the list of plants being returned.")
        BUGS = False
        return "Failed to add plant", 500
    
    plants = Plant.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': plant.id,
        'name': plant.name,
        'plant_type': plant.plant_type,
        'health_data': plant.health_data
    } for plant in plants])

@app.route('/trigger_bug', methods=['GET'])
def bug():
    logging.error("Triggering bug...")
    global BUGS
    BUGS = True
    return "Bug triggered", 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5002)
