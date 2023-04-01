from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(100))

    def __repr__(self):
        return f"{self.name}"