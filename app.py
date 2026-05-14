import re
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
import abc


db = SQLAlchemy()
login_manager = LoginManager()
#LOGIN DATABASE
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def password(self):
        raise AttributeError("Password is write-only")


# --- Authentication service abstraction and implementation ---
class AuthService(abc.ABC):
    @abc.abstractmethod
    def register(self, username, email, password, role):
        """Register a user. Return (user, errors)."""
        pass

    @abc.abstractmethod
    def authenticate(self, email, password):
        """Authenticate a user. Return user or None."""
        pass


class SqlAlchemyAuthService(AuthService):
    def register(self, username, email, password, role):
        errors = []
        if not(3 <= len(username) <= 64):
            errors.append(f"Username {username} must be between 3 and 64 characters")
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            errors.append(f"Email {email} must be a valid email address")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters")
        if errors:
            return None, errors
        try:
            user = User(username=username, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return user, []
        except IntegrityError:
            db.session.rollback()
            return None, ["Username or email already exists"]

    def authenticate(self, email, password):
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user
        return None


# --- Dashboard abstraction and concrete implementations ---
class BaseDashboard(abc.ABC):
    @abc.abstractmethod
    def render_redirect(self):
        pass


class OwnerDashboard(BaseDashboard):
    def render_redirect(self):
        return redirect(url_for('owner'))


class GuardDashboard(BaseDashboard):
    def render_redirect(self):
        return redirect(url_for('guard'))


class DashboardFactory:
    @staticmethod
    def for_role(role):
        if role == 'owner':
            return OwnerDashboard()
        return GuardDashboard()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    #DATABASE HEALTH CHECK
    @app.route('/health/db')
    def health_db():
        try:
            db.session.execute(text("SELECT 1"))
            return {'db': 'ok'}, 200

        except Exception as e:
            return {'db': 'error', 'detail': str(e)}, 500

    with app.app_context():
        db.create_all()

    # services
    auth_service = SqlAlchemyAuthService()


    #HOME PAGE
    @app.route('/')
    def index():
        return render_template("auth/login.html")
    #OWNER DASHBOARD
    @app.route('/owner')
    @login_required
    def owner():
        return render_template("dashboard/owner/dashboard.html")
    #GUARD DASHBOARD
    @app.route('/guard')
    @login_required
    def guard():
        return render_template("dashboard/guard/dashboard.html")


    #REGISTER DASHBOARD
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        error = []

        if request.method == 'POST':
            username = (request.form.get('username') or '').strip()
            email = (request.form.get('email') or '').strip()
            password = request.form.get('password') or ''
            confirm = request.form.get('confirm_password') or ''
            role = request.form.get('role') or ''

            if password != confirm:
                error.append("Password and confirm password must match")

            if not error:
                user, errs = auth_service.register(username=username, email=email, password=password, role=role)
                if errs:
                    error.extend(errs)
                else:
                    return redirect(url_for('login'))

        return render_template("auth/login.html", error=error)


    #LOGIN DASHBOARD
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
                user = auth_service.authenticate(email=email, password=password)
                if not user:
                    error.append("Invalid email or password")
                else:
                    login_user(user)
                    dashboard = DashboardFactory.for_role(user.role)
                    return dashboard.render_redirect()

        return render_template("auth/login.html", error=error)


    #LOG-OUT DASHBOARD
    @app.route('/logout')
    def logout():
        logout_user()
        flash('You have been logged out', 'success')
        return redirect(url_for('login'))

    #LOGIN MANAGER
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
