import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__)

    if os.environ.get('FLASK_ENV') == 'production':
        secret_key = os.environ.get('SECRET_KEY')
        db_uri = os.environ.get('SQLALCHEMY_DATABASE_URI')
        app.config['SECRET_KEY'] = secret_key
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    else:
        app.config.from_pyfile('config.py')
        # print mail config
        print(app.config['MAIL_SERVER'])
        print(app.config['MAIL_PORT'])
        print(app.config['MAIL_USE_SSL'])
        print(app.config['MAIL_USERNAME'])
        print(app.config['MAIL_PASSWORD'])
        

    db.init_app(app)
    mail.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    # from .main import main as main_blueprint
    # app.register_blueprint(main_blueprint)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()