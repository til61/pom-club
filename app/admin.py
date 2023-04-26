from flask import Blueprint, request, jsonify, session, render_template, abort, flash
from werkzeug.security import check_password_hash
from flask_login import login_user
from .models import User, Post
from . import db

admin = Blueprint('admin', __name__)

def admin_required(func):
    def wrapper(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'admin':
            # If the user is not logged in or does not have the 'admin' role,
            # redirect them to the login page or return an error message.
            # In this example, we'll just return a 403 Forbidden error.
            return abort(403)
        return func(*args, **kwargs)
    return wrapper

@admin.route("/getstatus")
def get_status():
    return render_template("status.html")

@admin.route("/admin", methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template("admin.html")
    if request.method == 'POST':
        username = request.form.get('username', None)
        password = request.form.get('password', None)
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password) or user.role != 'admin':
            abort(403)
        login_user(user)
        session['role'] = user.role
        return render_template("admin.html")


@admin_required
@admin.route("/admin/users")
def show_all_users():
    users = User.query.paginate(page=1, per_page=10, error_out=False)
    return render_template("users.html", users=users, page=1)

@admin_required
@admin.route("/admin/posts")
def show_all_posts():
    posts = Post.query.paginate(page=1, per_page=10, error_out=False)
    return render_template("posts.html", posts=posts, page=1)

@admin_required
@admin.route("/admin/users/<int:user_id>", methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=1, per_page=10, error_out=False)
    users_list = users.items
    return render_template("users.html", users=users_list, page=page)

@admin_required
@admin.route("/admin/posts/<int:post_id>", methods=['GET'])
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    comments = post.comments
    top_level_comments = [comment for comment in comments if not comment.parent_id]
    return render_template("post.html", post=post, top_level_comments=top_level_comments)

@admin_required
@admin.route("/admin/posts/<int:post_id>", methods=['POST'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    page = request.args.get('page', 1, type=int)
    posts = Post.query.paginate(page=1, per_page=10, error_out=False)
    post_list = posts.items
    return render_template("posts.html", posts=post_list, page=page)


# @admin.route("/admin/checklogin", methods=['POST'])
# def check_login():
#     token = request.json.get('token', None)
#     if 'token' in session:
#         if token == session['token']:
#             return jsonify({"message": "JWT secured"}), 200
#         else:
#             return jsonify({"message": "JWT mismatch"}), 409
#     else:
#         return jsonify({"message": "not logged in"}), 401