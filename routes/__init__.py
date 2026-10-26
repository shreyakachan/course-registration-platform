from routes.main import main_bp
from routes.auth import auth_bp
from routes.courses import courses_bp
from routes.student import student_bp
from routes.admin import admin_bp
from routes.errors import errors_bp

__all__ = [
    'main_bp',
    'auth_bp',
    'courses_bp',
    'student_bp',
    'admin_bp',
    'errors_bp'
]
