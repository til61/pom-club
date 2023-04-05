from flask import Blueprint, request, jsonify, session, current_app, render_template

admin = Blueprint('admin', __name__)

@admin.route("/getstatus")
def get_status():
    return render_template("status.html")