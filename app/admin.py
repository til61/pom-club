from flask import Blueprint, request, jsonify, session, current_app, render_template

admin = Blueprint('admin', __name__)

@admin.route("/getstatus")
def get_status():
    return render_template("status.html")

# @admin.route("/getusers")
# def get_users():
#     pass

# @admin.route("/getposts")
# def get_posts():
#     pass

# @admin.route("/getcomments")
# def get_comments():
#     pass

@admin.route("/checklogin")
def check_login():
    if 'token' in session:
        return jsonify({"message": "logged in"}), 200
    else:
        return jsonify({"message": "not logged in"}), 401