from flask_login import login_user, login_required, logout_user
from flask import Blueprint, request, jsonify, session, current_app, abort
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db, mail
from flask_mail import Mail, Message
import secrets
import jwt
import os

auth = Blueprint('auth', __name__)
secret_key = os.getenv('SECRET_KEY')

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
        token = jwt.encode({'user_id': user.id}, secret_key, algorithm='HS256')
        session['token'] = token
        session['role'] = user.role
        return jsonify({"message": "Login successful",
                        "token": token}), 200
    
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
            return jsonify({"message": "Username already exists"}), 409
        if password.__len__() < 8:
            return jsonify({"message": "Password must be at least 8 characters long"}), 400

        code = secrets.token_hex(4)
        msg = Message('(波姆社)邮箱地址验证', sender='咕咕菇 <972648237@qq.com>', recipients=[email])
        msg.body = f"您的验证码是：{code}，有效时间大约30分钟。邮箱有人看，反馈bug也可以发到这个地址。"
        msg.charset = 'utf-8'
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
            new_user = User(username=session['username'], password=session['password'], email=session['email'], role='user')
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
    session.pop('token', None)
    return jsonify({"message": "User logged out successfully"}), 200
