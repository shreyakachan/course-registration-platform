from models.user import User
from extensions import db

def test_valid_login_succeeds(client):
    """Test successful authentication for registered student."""
    res = client.post('/login', data={
        'email': 'alice@test.edu',
        'password': 'StudentPass123!'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Welcome back, Alice Student!" in res.data
    assert b"Student Dashboard" in res.data

def test_invalid_login_fails(client):
    """Test that incorrect credentials produce an error and reject login."""
    res = client.post('/login', data={
        'email': 'alice@test.edu',
        'password': 'WrongPassword999'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Invalid email or password" in res.data

def test_logout_clears_session(student_client):
    """Test that user logout terminates authenticated session."""
    res = student_client.post('/logout', follow_redirects=True)
    assert res.status_code == 200
    assert b"You have been successfully logged out" in res.data

    # Verify student can no longer access protected dashboard
    protected_res = student_client.get('/dashboard', follow_redirects=False)
    assert protected_res.status_code == 302
    assert '/login' in protected_res.headers['Location']

def test_unauthenticated_cannot_access_protected_routes(client):
    """Test that anonymous users are redirected to login for protected endpoints."""
    protected_endpoints = ['/dashboard', '/my-registrations', '/profile', '/admin/dashboard']
    for ep in protected_endpoints:
        res = client.get(ep, follow_redirects=False)
        assert res.status_code == 302
        assert '/login' in res.headers['Location']

def test_student_cannot_access_admin_dashboard(student_client):
    """Test that students are forbidden (HTTP 403) from accessing admin routes."""
    res = student_client.get('/admin/dashboard')
    assert res.status_code == 403
    assert b"Access Forbidden" in res.data

def test_student_registration_and_duplicate_prevention(client, app):
    """Test student self-registration and rejection of duplicate email addresses."""
    # Register new student
    res = client.post('/register', data={
        'name': 'Charlie Brown',
        'email': 'charlie@test.edu',
        'password': 'CharliePass123!',
        'confirm_password': 'CharliePass123!'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Registration successful" in res.data

    # Verify user exists in database with hashed password
    with app.app_context():
        user = User.query.filter_by(email='charlie@test.edu').first()
        assert user is not None
        assert user.name == 'Charlie Brown'
        assert user.check_password('CharliePass123!')
        assert user.password_hash != 'CharliePass123!'

    # Log out Charlie so that the /register endpoint is not bypassed by existing session
    client.post('/logout', follow_redirects=True)

    # Attempt duplicate registration with same email
    dup_res = client.post('/register', data={
        'name': 'Charlie Duplicate',
        'email': 'charlie@test.edu',
        'password': 'AnotherPassword123!',
        'confirm_password': 'AnotherPassword123!'
    }, follow_redirects=True)
    assert b"An account with this email address already exists" in dup_res.data
