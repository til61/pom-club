from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from . import db

class User(UserMixin, db.Model):
    """Model representing a user in the system."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(10), nullable=False)
    posts = relationship('Post', backref='author', lazy=True)
    comments = relationship('Comment', backref='author', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'posts': [post.to_dict() for post in self.posts],
            'comments': [comment.to_dict() for comment in self.comments]
        }

class Post(db.Model):
    """Model representing a post in the system."""

    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    content = Column(Text)
    timestamp = Column(DateTime)
    author_id = Column(Integer, ForeignKey('users.id'))
    images = relationship('Image', backref='post', lazy=True)
    comments = relationship('Comment', backref='post', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'author_id': self.author_id,
            'image_link': self.image_link,
            'comments': [comment.to_dict() for comment in self.comments]
        }

class Comment(db.Model):
    """Model representing a comment in the system."""

    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    content = Column(Text)
    timestamp = Column(DateTime)
    images = relationship('Image', backref='comment', lazy=True)
    author_id = Column(Integer, ForeignKey('users.id'))
    post_id = Column(Integer, ForeignKey('posts.id'))
    parent_id = Column(Integer, ForeignKey('comments.id'))
    children = relationship('Comment', cascade='all, delete-orphan',
                        backref=backref('parent', remote_side=[id]),
                        lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'image_link': self.image_link,
            'author_id': self.author_id,
            'post_id': self.post_id,
            'parent_id': self.parent_id,
            'children': [child.to_dict() for child in self.children]
        }
    
class Image(db.Model):
    """Model representing an image in the system."""

    __tablename__ = 'images'

    id = Column(Integer, primary_key=True)
    image_link = Column(Text, nullable=False)
    uploader_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=True)
    comment_id = Column(Integer, ForeignKey('comments.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'image_link': self.image_link,
            'uploader_id': self.uploader_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'post_id': self.post_id,
            'comment_id': self.comment_id,
        }
    
class UserPostHistory(db.Model):
    """Model representing a user's post history in the system."""

    __tablename__ = 'user_post_history'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    post_id = Column(Integer, ForeignKey('posts.id'))
    timestamp = Column(DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'timestamp': self.timestamp
        }


class Upvote(db.Model):
    """Model representing an upvote in the system."""

    __tablename__ = 'upvotes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    post_id = Column(Integer, ForeignKey('posts.id'))
    comment_id = Column(Integer, ForeignKey('comments.id'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'comment_id': self.comment_id
        }

    