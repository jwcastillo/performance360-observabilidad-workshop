# user_service.py

from flask import Flask, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)
app.config['SECRET_KEY'] = 'plantsarecool1234'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db:5432/user_service_db'
db = SQLAlchemy(app)

BUGS = False

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password_hash=hashed_password)

    global BUGS
    if BUGS == True:
        logging.error("What a nasty bug! It flew into the user service and stopped the user being created.")
        BUGS = False
        return "Failed to create user", 500
    try:
        db.session.add(new_user)
        db.session.commit()
        logging.info(f"New user created: {username}")
        return jsonify({"message": "Signup successful"}), 200
    except IntegrityError:
        db.session.rollback()
        logging.error(f"Signup failed: Username '{username}' already exists.")
        return jsonify({"error": "That username is already taken, please choose another."}), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f"An unexpected error occurred during signup:{str(e)}")
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

@app.route('/login', methods=['POST'])
def login():
    global BUGS
    if BUGS == True:
        logging.error("What a nasty bug! It flew into the user service and stopped the user being created.")
        BUGS = False
        return "Failed to login", 500
    
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        return jsonify({"user_id": user.id}), 200
    return jsonify({"error": "Login failed"}), 401

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logout successful"}), 200

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"id": user.id, "username": user.username}), 200


@app.route('/trigger_bug', methods=['GET'])
def bug():
    logging.error("Triggering bug...")
    global BUGS
    BUGS = True
    return "Bug triggered", 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5001)
