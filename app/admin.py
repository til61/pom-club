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

@admin.route("/checklogin", methods=['POST'])
def check_login():
    token = request.json.get('token', None)
    if 'token' in session:
        if token == session['token']:
            return jsonify({"message": "JWT secured"}), 200
        else:
            return jsonify({"message": "JWT mismatch"}), 409
    else:
        return jsonify({"message": "not logged in"}), 401