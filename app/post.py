from flask import Blueprint, request, jsonify, session
from flask_login import login_required
from .models import User, Post, Comment
from . import db
from datetime import datetime
from functools import wraps
import os
import jwt

post = Blueprint('post', __name__)
secret_key = os.getenv('SECRET_KEY')

def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.headers.get('token')

        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        if token != session.get('token'):
            return jsonify({'error': 'Invalid token'}), 401

        return func(*args, **kwargs)

    return decorated

@login_required
@token_required
@post.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json()

    # Ensure that required fields are present in the request
    if not all(key in data for key in ['title', 'content', 'author_id']):
        return jsonify({'error': 'Missing required fields'}), 400

    # Create a new post object
    new_post = Post(
        title=data['title'],
        content=data['content'],
        author_id=data['author_id'],
        timestamp=datetime.utcnow(),
        image_link=data.get('image_link')
    )

    # Add the new post to the database
    db.session.add(new_post)
    db.session.commit()

    return jsonify({'message': 'Post created successfully'}), 201

@login_required
@token_required
@post.route('/posts', methods=['GET'])
def get_posts():
    posts = Post.query.all()
    return jsonify([post.to_dict() for post in posts]), 200

@login_required
@token_required
@post.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.get(post_id)

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    post_dict = post.to_dict()
    comments = get_comments(post.comments)
    post_dict['comments'] = comments

    return jsonify({'post': post_dict})

    
@login_required
@token_required
@post.route('/posts/<int:author_id>', methods=['GET'])
def get_posts_by_author(author_id):
    author = User.query.get(author_id)

    if not author:
        return jsonify({'error': 'Author not found'}), 404

    posts = Post.query.filter_by(author_id=author_id).all()

    post_data = []
    for post in posts:
        post_dict = post.to_dict()
        comments = get_comments(post.comments)
        post_dict['comments'] = comments
        post_data.append(post_dict)

    return jsonify({'posts': post_data})

@login_required
@token_required
@post.route('/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    current_user_id = session.get('user_id')
    post = Post.query.get(post_id)

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    data = request.get_json()
    content = data.get('content')
    parent_id = data.get('parent_id')

    if not content:
        return jsonify({'error': 'Comment content is required'}), 400

    if parent_id:
        parent_comment = Comment.query.get(parent_id)

        if not parent_comment:
            return jsonify({'error': 'Parent comment not found'}), 404

        comment = Comment(content=content, author_id=current_user_id, post_id=post_id, parent_id=parent_id)
    else:
        comment = Comment(content=content, author_id=current_user_id, post_id=post_id)

    db.session.add(comment)
    db.session.commit()

    return jsonify({'comment_id': comment.id}), 201



def get_comments(comments):
    comments_data = []
    for comment in comments:
        comment_dict = comment.to_dict()
        children = get_comments(comment.children)
        if children:
            comment_dict['children'] = children
        comments_data.append(comment_dict)
    return comments_data

