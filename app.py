from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @app.route('/')
    def index():
        return render_template("auth/login.html")

    @app.route('/login')
    def login():
        return render_template("auth/login.html")

    @login_manager.user_loader
    def load_user(user_id):
        return None

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5555 )
