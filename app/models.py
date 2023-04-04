from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from . import db

class User(UserMixin, db.Model):
    """Model representing a user in the system."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True)
    password = Column(String(255))
    email = Column(String(255), unique=True)
    posts = relationship('Post', backref='author', lazy=True)
    comments = relationship('Comment', backref='author', lazy=True)

class Post(db.Model):
    """Model representing a post in the system."""

    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    content = Column(Text)
    timestamp = Column(DateTime)
    author_id = Column(Integer, ForeignKey('users.id'))
    comments = relationship('Comment', backref='post', lazy=True)

class Comment(db.Model):
    """Model representing a comment in the system."""

    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    content = Column(Text)
    timestamp = Column(DateTime)
    author_id = Column(Integer, ForeignKey('users.id'))
    post_id = Column(Integer, ForeignKey('posts.id'))
    parent_id = Column(Integer, ForeignKey('comments.id'))
    parent = relationship('Comment', remote_side=[id])
