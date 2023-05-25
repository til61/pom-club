from flask import Blueprint, request, jsonify, session, render_template, abort, flash
from werkzeug.utils import secure_filename
from .models import User, Post, Comment, UserPostHistory, Upvote, Image
from . import db
from datetime import datetime
from functools import wraps
import os
import jwt
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy.sql.expression import func
import boto3
import uuid
from dotenv import load_dotenv

post = Blueprint('post', __name__)
load_dotenv()
secret_key = os.getenv('SECRET_KEY')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'flv'}
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

# Create the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create the file handler and add it to the logger
handler = RotatingFileHandler('post.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.headers.get('token')

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        return func(*args, **kwargs)

    return decorated

def get_user_id(token):
    try:
        data = jwt.decode(token, secret_key, algorithms=['HS256'])
        logger.info(f"{datetime.utcnow()}: User {data['user_id']} accessed the post API")
        return data['user_id']
    except:
        logger.info(f"{datetime.utcnow()}Invalid token {token} used")
        return None

@post.route('/addpost', methods=['POST'])
@token_required
def add_post():
    data = request.get_json()

    # Ensure that required fields are present in the request
    if not all(key in data for key in ['title', 'content']):
        return jsonify({
            "code": 0,
            'message': 'Missing required fields'}), 200
    
    # Get the user from the token
    user_id = get_user_id(request.headers.get('token'))

    # Create a new post object
    new_post = Post(
        title=data['title'],
        content=data['content'],
        author_id=user_id,
        timestamp=datetime.utcnow(),
    )

    # Add the new post to the database
    db.session.add(new_post)
    db.session.commit()

    return jsonify({
        "code": 1,
        'message': 'Post created successfully'}), 201

# deprecated because we are moving to MVC
# @post.route('/posts', methods=['GET'])
# @token_required
# def get_posts():
#     posts = Post.query.all()
#     return jsonify([post.to_dict() for post in posts]), 200

@post.route('/posts/post=<int:post_id>', methods=['GET'])
@token_required
def view_post(post_id):
    # post = Post.query.get(post_id)
    
    # if not post:
    #     return jsonify({
    #         "code": 0,
    #         'message': 'Post not found'}), 200

    # post_dict = post.to_dict()
    # comments = get_comments(post.comments)
    # post_dict['comments'] = comments

    post = Post.query.get_or_404(post_id)
    comments = post.comments
    top_level_comments = [comment for comment in comments if not comment.parent_id]
    return render_template("user/post.html", post=post, top_level_comments=top_level_comments)

    # add post to user history
    user_id = get_user_id(request.headers.get('token'))
    history = UserPostHistory(user_id=user_id, post_id=post_id, timestamp=datetime.utcnow())
    db.session.merge(history)
    db.session.commit()


    return jsonify({
        "code": 1,
        'post': post_dict})

    
@post.route('/posts/author=<int:author_id>', methods=['GET'])
@token_required
def get_posts_by_author(author_id):
    author = User.query.get(author_id)

    if not author:
        return jsonify({
            "code": 0,
            'message': 'Author not found'}), 200

    posts = Post.query.filter_by(author_id=author_id).all()

    post_data = []
    for post in posts:
        post_dict = {"id": post.id, 
                     "title": post.title, 
                     "content": post.content, 
                     "timestamp": post.timestamp
                     }
        post_data.append(post_dict)

    return jsonify({'posts': post_data})

@post.route('/posts/post=<int:post_id>/addcomment', methods=['POST'])
@token_required
def add_comment(post_id):
    post = Post.query.get(post_id)

    if not post:
        return jsonify({
            "code": 0,
            'message': 'Post not found'}), 200
    
    user_id = get_user_id(request.headers.get('token'))

    data = request.get_json()
    content = data.get('content')
    parent_id = data.get('parent_id')

    if not content:
        return jsonify({
            "code": 0,
            'message': 'Comment content is required'}), 200

    if parent_id:
        parent_comment = Comment.query.get(parent_id)

        if not parent_comment:
            return jsonify({
                "code": 0,
                'message': 'Parent comment not found'}), 200

        comment = Comment(
            content=content, 
            timestamp=datetime.utcnow(),
            author_id=user_id, 
            post_id=post_id, 
            parent_id=parent_id)
    else:
        comment = Comment(
            content=content, 
            timestamp=datetime.utcnow(),
            author_id=user_id, 
            post_id=post_id)

    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "code": 1,
        'message': comment.id}), 201

@post.route('/posts/post=<int:post_id>/upvote', methods=['POST'])
@token_required
def upvote_post(post_id):
    post = Post.query.get(post_id)

    if not post:
        return jsonify({
            "code": 0,
            'message': 'Post not found'}), 200

    user_id = get_user_id(request.headers.get('token'))

    upvote = Upvote.query.filter_by(post_id=post_id, user_id=user_id).first()

    if upvote:
        db.session.delete(upvote)
        db.session.commit()
        return jsonify({
            "code": 1,
            'message': 'Upvote removed'}), 200

    new_upvote = Upvote(post_id=post_id, user_id=user_id)
    db.session.add(new_upvote)
    db.session.commit()

    return jsonify({
        "code": 1,
        'message': 'Upvote added'}), 201

@post.route('/posts/post=<int:post_id>/upvotes', methods=['GET'])
@token_required
def get_upvotes(post_id):
    post = Post.query.get(post_id)

    if not post:
        return jsonify({
            "code": 0,
            'message': 'Post not found'}), 200

    upvotes = Upvote.query.filter_by(post_id=post_id).all()

    upvote_data = []
    for upvote in upvotes:
        upvote_dict = {"id": upvote.id, 
                       "user_id": upvote.user_id, 
                       "post_id": upvote.post_id
                       }
        upvote_data.append(upvote_dict)

    return jsonify({
        "code": 1,
        'upvotes': upvote_data}), 200


@post.route('/home', methods=['GET'])
@token_required
def get_home():
    user_id = get_user_id(request.headers.get('token'))
    user = User.query.get(user_id)

    # for now just get all the posts by time
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page=1, per_page=10, error_out=False)
    return render_template('user/home.html', posts=posts, page=1)


@post.route('/uploadImg', methods=['POST'])
def upload_img():
    file = request.files['file']
    if file and file.filename != '':
        if allowed_file(file.filename):
            boto_session = boto3.Session(
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_ACCESS_KEY,
            )
            s3 = boto_session.resource('s3')
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            filename = str(uuid.uuid4()) + '.' + file_extension
            s3.Bucket(S3_BUCKET_NAME).put_object(Key=filename, Body=file)
            return jsonify({
                "code": 1,
                'message': filename}), 200
        else:
            return jsonify({
                "code": 0,
                'message': 'File type not allowed'}), 200
    else:
        return jsonify({
            "code": 0,
            'message': 'No file found'}), 200
    

@post.route('/createPost', methods=['GET', 'POST'])
def create_post():
    if request.method == "GET":
        user_id = get_user_id(request.headers.get('token'))
        session['user_id'] = user_id
        return render_template('user/editor.html')
    elif request.method == "POST":
        user_id = session.get('user_id')
        title = request.form.get('title')
        content = request.form.get('content')
        images = request.form.getlist('images')
        if not title:
            return jsonify({
                "code": 0,
                'message': 'Post title is required'}), 200
        if not content:
            return jsonify({
                "code": 0,
                'message': 'Post content is required'}), 200
        post = Post(title=title, content=content, timestamp=datetime.utcnow(), author_id=user_id)
        db.session.add(post)
        db.session.commit()
        if images:
            images=images[0].split(',')
            for image in images:
                new_image = Image(post_id=post.id, 
                                  image_link=image,
                                  timestamp=datetime.utcnow(),
                                  uploader_id=user_id
                                  )
                db.session.add(new_image)
                db.session.commit()
        return jsonify({
            "code": 1,
            'message': post.id}), 201
    





def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_comments(comments):
    comments_data = []
    for comment in comments:
        if not comment.parent_id:
            comment_dict = comment.to_dict()
            children = get_comments(comment.children)
            if children:
                comment_dict['children'] = children
            comments_data.append(comment_dict)
    return comments_data

def get_recommendations_for_user(user_id, num_recommendations=5):
    # Retrieve all the posts that the user has liked or upvoted
    user_upvotes = Upvote.query.filter_by(user_id=user_id).all()

    # Retrieve the IDs of the posts that the user has liked or upvoted
    post_ids = [upvote.post_id for upvote in user_upvotes]

    # Retrieve all the upvotes for the same posts that the user has liked or upvoted
    related_upvotes = Upvote.query.filter(Upvote.post_id.in_(post_ids)).all()

    # Create a dictionary to count the number of times each post has been liked or upvoted
    post_counts = {}
    for upvote in related_upvotes:
        post_id = upvote.post_id
        if post_id not in post_counts:
            post_counts[post_id] = 0
        post_counts[post_id] += 1

    # Sort the posts by the number of times they have been liked or upvoted
    sorted_posts = sorted(post_counts.items(), key=lambda x: x[1], reverse=True)

    # Retrieve the top N posts
    top_posts = [Post.query.get(post_id) for post_id, _ in sorted_posts[:num_recommendations]]

    # Return the top N posts as a list of dictionaries
    return [post.to_dict() for post in top_posts]

def get_recommendations_based_on_history(user_id, num_recommendations=5):
    # Retrieve the user's browsing history
    user_history = UserPostHistory.query.filter_by(user_id=user_id).all()

    # Retrieve the IDs of the posts that the user has viewed
    post_ids = [history.post_id for history in user_history]

    # Retrieve all the browsing history for the same posts that the user has viewed
    related_history = UserPostHistory.query.filter(UserPostHistory.post_id.in_(post_ids)).all()

    # Create a dictionary to count the number of times each post has been viewed
    post_counts = {}
    for history in related_history:
        post_id = history.post_id
        if post_id not in post_counts:
            post_counts[post_id] = 0
        post_counts[post_id] += 1

    # Sort the posts by the number of times they have been viewed
    sorted_posts = sorted(post_counts.items(), key=lambda x: x[1], reverse=True)

    # Retrieve the top N posts
    top_posts = [Post.query.get(post_id) for post_id, _ in sorted_posts[:num_recommendations]]

    # Return the top N posts as a list of dictionaries
    return [post.to_dict() for post in top_posts]




