from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager

class User(UserMixin, db.Model):
    """User account model for Students and Administrators."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student' or 'admin'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    registrations = db.relationship(
        'Registration',
        back_populates='student',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    def set_password(self, password):
        """Hashes password with salted Werkzeug pbkdf2."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies supplied password against hash."""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Returns True if the user has administrator privileges."""
        return self.role == 'admin'

    def is_student(self):
        """Returns True if the user is a student."""
        return self.role == 'student'

    def __repr__(self):
        return f"<User id={self.id} email='{self.email}' role='{self.role}'>"

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader callback."""
    return db.session.get(User, int(user_id))
