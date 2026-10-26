import os
import tempfile
import pytest
from app import create_app
from extensions import db
from models.user import User
from models.course import Course
from models.registration import Registration

@pytest.fixture
def app():
    """Create and configure a new app instance with an isolated temporary SQLite database for each test."""
    db_fd, db_path = tempfile.mkstemp(suffix='_test.db')
    os.close(db_fd)

    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key-123'
    })

    with app.app_context():
        db.create_all()

        # Seed test admin
        admin = User(name='Test Admin', email='admin@test.edu', role='admin')
        admin.set_password('AdminPass123!')
        db.session.add(admin)

        # Seed primary test student
        student = User(name='Alice Student', email='alice@test.edu', role='student')
        student.set_password('StudentPass123!')
        db.session.add(student)

        # Seed secondary test student (for unauthorized cross-user tests)
        student2 = User(name='Bob Student', email='bob@test.edu', role='student')
        student2.set_password('BobPass123!')
        db.session.add(student2)

        # Seed test courses
        # Course 1: Normal capacity (10 seats)
        c1 = Course(
            code='CS101',
            title='Intro to Computer Science',
            category='Computer Science',
            instructor='Prof. Turing',
            credits=3,
            duration='12 Weeks',
            capacity=10,
            description='Foundational computer science principles and algorithms.'
        )
        # Course 2: Low capacity (1 seat) for testing seat limits
        c2 = Course(
            code='K8S101',
            title='Container Engineering',
            category='Cloud & DevOps',
            instructor='Prof. Docker',
            credits=4,
            duration='10 Weeks',
            capacity=1,
            description='Kubernetes cluster administration and container deployment.'
        )
        db.session.add_all([c1, c2])
        db.session.commit()

    yield app

    # Teardown: close sessions and remove temporary database file
    with app.app_context():
        db.session.remove()
        db.drop_all()

    if os.path.exists(db_path):
        try:
            os.unlink(db_path)
        except OSError:
            pass

@pytest.fixture
def client(app):
    """Anonymous HTTP client."""
    return app.test_client()

@pytest.fixture
def student_client(app):
    """Authenticated client for the primary student (alice@test.edu)."""
    c = app.test_client()
    with app.app_context():
        c.post('/login', data={'email': 'alice@test.edu', 'password': 'StudentPass123!'}, follow_redirects=True)
    return c

@pytest.fixture
def student2_client(app):
    """Authenticated client for the secondary student (bob@test.edu)."""
    c = app.test_client()
    with app.app_context():
        c.post('/login', data={'email': 'bob@test.edu', 'password': 'BobPass123!'}, follow_redirects=True)
    return c

@pytest.fixture
def admin_client(app):
    """Authenticated client for the administrator (admin@test.edu)."""
    c = app.test_client()
    with app.app_context():
        c.post('/login', data={'email': 'admin@test.edu', 'password': 'AdminPass123!'}, follow_redirects=True)
    return c
