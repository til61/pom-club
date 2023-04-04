from flask_login import login_user, login_required, logout_user
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db, mail
from flask_mail import Mail, Message
import secrets

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['POST'])
def login():
    # login code goes here
    if request.is_json:
        username = request.json.get('username', None)
        password = request.json.get('password', None)
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({"message": "Bad username or password"}), 401  # unauthorized
        login_user(user)
        return jsonify({"message": "Login successful"}), 200
    
    return jsonify({"message": "Missing JSON in request"}), 400

@auth.route('/signup', methods=['POST'])
def signup():
    # code to validate and add user to database goes here
    if request.is_json:
        username = request.json.get('username', None)
        password = request.json.get('password', None)
        email = request.json.get('email', None)
        
        # check if user already exists
        user_by_name = User.query.filter_by(username=username).first()
        if user_by_name:
            return jsonify({"message": "Username already exists"}), 401
        if password.__len__() < 8:
            return jsonify({"message": "Password must be at least 8 characters long"}), 401

        code = secrets.token_hex(4)
        msg = Message('Verify your email', sender='til61atg@gmail.com', recipients=[email])
        msg.body = f"Your verification code is {code}"
        mail.send(msg)
        # store user data in session
        session['username'] = username
        session['password'] = generate_password_hash(password, method='sha256')
        session['code'] = code
        session['email'] = email

        return jsonify({"message": "email verification sent"}), 200
    else:
        return jsonify({"message": "Missing JSON in request"}), 400
    
@auth.route('/verify', methods=['POST'])
def verify():
    if request.is_json:
        code = request.json.get('code', None)
        if code == session['code']:
            new_user = User(username=session['username'], password=session['password'], email=session['email'])
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"message": "User verified successfully"}), 200
        else:
            return jsonify({"message": "Invalid code"}), 401
    else:
        return jsonify({"message": "Missing JSON in request"}), 400

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"message": "User logged out successfully"}), 200