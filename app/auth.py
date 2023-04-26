from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db, mail
from flask_mail import Mail, Message
import secrets
import jwt
import os
import redis
import uuid
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

auth = Blueprint('auth', __name__)
secret_key = os.getenv('SECRET_KEY')

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Create the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create the file handler and add it to the logger
handler = RotatingFileHandler('post.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

def generate_session_id():
    return str(uuid.uuid4())

@auth.route('/login', methods=['POST'])
def login():
    # login code goes here
    if request.is_json:
        username = request.json.get('username', None)
        password = request.json.get('password', None)
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            logger.info(f"{datetime.utcnow()}: Invalid login attempt for {username}")
            return jsonify({"code": 0, "message": "Bad username or password"}), 200
        token = jwt.encode({'user_id': user.id}, secret_key, algorithm='HS256')
        logger.info(f"{datetime.utcnow()}: {user.id} logged in")
        return jsonify({"code": 1, 
                        "message": "Login successful",
                        "token": token}), 200
    
    return jsonify({"code": -1, "message": "Missing JSON in request"}), 200

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
            return jsonify({"code": 0, 
                            "message": "Username already exists"}), 200
        user_by_email = User.query.filter_by(email=email).first()
        if user_by_email:
            return jsonify({"code": 0, 
                            "message": "Email already exists"}), 200
        if password.__len__() < 8:
            return jsonify({"code": 0,
                            "message": "Password must be at least 8 characters long"}), 200

        code = secrets.token_hex(2)
        msg = Message('(波姆社)邮箱地址验证', sender='咕咕菇 <972648237@qq.com>', recipients=[email])
        msg.body = f"您的验证码是：{code}，有效时间大约30分钟。邮箱有人看，反馈bug也可以发到这个地址。"
        msg.charset = 'utf-8'
        mail.send(msg)
        # store user data in redis session
        # Generate a new session ID
        session_id = generate_session_id()
        # Use the session ID
        redis_client.set(session_id, 
                         json.dumps({'username': username, 
                                     'password': generate_password_hash(password, method='sha256'), 
                                     'code': code, 
                                     'email': email}))
        # Set the expiration of the session ID
        redis_client.expire(session_id, 1800) # 30 minutes
        logger.info(f"{datetime.utcnow()}: {username} signed up")
        return jsonify({"code": 1, 
                        "message": "email verification sent",
                        "cookie": session_id}), 200
    else:
        return jsonify({"code": -1,
                        "message": "Missing JSON in request"}), 200
    
@auth.route('/verify', methods=['POST'])
def verify():
    if request.is_json:
        code = request.json.get('code', None)
        session_id = request.json.get('cookie', None)
        session = redis_client.get(session_id)
        if session:
            session = json.loads(session)
        else:
            logger.info(f"{datetime.utcnow()}: Invalid session ID")
            return jsonify({"code": 0, "message": "Invalid session ID"}), 200
        stored_code = session['code']
        stored_username = session['username']
        stored_password = session['password']
        stored_email = session['email']
        if code == stored_code:
            new_user = User(username=stored_username, 
                            password=stored_password, 
                            email=stored_email, role='user')
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"{datetime.utcnow()}: {stored_username} verified")
            return jsonify({"code": 1, "message": "User verified successfully"}), 200
        else:
            return jsonify({"code": 0, "message": "Invalid verification code"}), 200
    else:
        return jsonify({"code": -1, "message": "Missing JSON in request"}), 200

# since we are using JWTs...
# @auth.route('/logout')
# def logout():
#     return jsonify({"code": 1, "message": "User logged out successfully"}), 200
