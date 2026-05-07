from flask import Flask, render_template, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from sqlalchemy import text
import re

db = SQLAlchemy()
login_manager = LoginManager()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @app.route('/health/db')
    def health_db():
        try:
            db.session.execute(text("SELECT 1"))
            return {'db': 'ok'}, 200

        except Exception as e:
            return {'db': 'error', 'detail': str(e)}, 500

    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        return render_template("auth/login.html")

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        error = []

        if request.method == 'POST':
            username = (request.form['username']or '').strip()
            email = (request.form['email']).strip()
            password = request.form['password']or ''
            confirm = request.form['confirm_password']or ''
            role = request.form['role']

            if not(3 <= len(username) <= 64):
                error.append(f"Username {username} must be between 3 and 64 characters")
            if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
                error.append(f"Email {email} must be a valid email address")
            if len(password) < 6:
                error.append(f"Password must be at least 6 characters")
            if password != confirm:
                error.append(f"Password and confirm password must match")

            if not error:
                return f'valid input received'


            #return f"receive data - {email}"
        return render_template("auth/login.html", error=error)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        return render_template("auth/login.html")

    @login_manager.user_loader
    def load_user(user_id):
        return None

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5555 )
