import re
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()
login_manager = LoginManager()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(64), nullable=False)

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

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template("dashboard/dashboard.html")
    @app.route('/owner')
    @login_required
    def owner():
        return render_template("dashboard/owner.html")
    @app.route('/guard')
    @login_required
    def guard():
        return render_template("dashboard/guard.html")

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        error = []

        if request.method == 'POST':
            # use .get to avoid KeyError when a field is missing
            username = (request.form.get('username') or '').strip()
            email = (request.form.get('email') or '').strip()
            password = request.form.get('password') or ''
            confirm = request.form.get('confirm_password') or ''
            role = request.form.get('role') or ''

            if not(3 <= len(username) <= 64):
                error.append(f"Username {username} must be between 3 and 64 characters")
            if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
                error.append(f"Email {email} must be a valid email address")
            if len(password) < 6:
                error.append(f"Password must be at least 6 characters")
            if password != confirm:
                error.append(f"Password and confirm password must match")

            if not error:
                try:
                    pwd_hash = generate_password_hash(password)
                    user = User(username=username, email=email, password_hash=pwd_hash, role=role)
                    db.session.add(user)
                    db.session.commit()

                    return redirect(url_for('login'))

                except IntegrityError:
                    db.session.rollback()
                    error.append(f"Username or email already exists")

        return render_template("auth/login.html", error=error)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = []

        if request.method == 'POST':
            email = (request.form.get('email') or '').strip()
            password = request.form.get('password') or ''

            if not email:
                error.append("Email must be provided")
            if not password:
                error.append("Password must be provided")
            if not error:
                user = User.query.filter_by(email=email).first()
                if not user or not check_password_hash(user.password_hash, password):
                    error.append("Invalid email or password")
                else:
                    login_user(user)
                    if user.role == 'owner':
                        return redirect(url_for('owner'))
                    return redirect(url_for('guard'))

        return render_template("auth/login.html", error=error)

    @app.route('/logout')
    def logout():
        logout_user()
        flash('You have been logged out', 'success')
        return redirect(url_for('login'))

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5555 )
