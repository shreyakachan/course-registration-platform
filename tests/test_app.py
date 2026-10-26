import os
import tempfile
import pytest
from app import create_app, get_db_connection

@pytest.fixture
def app():
    """Create and configure a new application instance with an isolated temporary SQLite database for each test."""
    db_fd, db_path = tempfile.mkstemp(suffix='_test.db')
    os.close(db_fd)

    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
        'SECRET_KEY': 'test-secret-key-automation-123'
    })

    yield app

    # Clean up temporary database file
    if os.path.exists(db_path):
        try:
            os.unlink(db_path)
        except OSError:
            pass

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_home_page_status_and_content(client):
    """Test that the home page returns HTTP 200 and renders course catalog."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Course Registration" in response.data
    assert b"DEV101" in response.data
    assert b"Cloud" in response.data
    assert b"DevOps Fundamentals" in response.data
    assert b"Available Courses" in response.data

def test_health_endpoint_healthy(client):
    """Test that the /health endpoint returns HTTP 200 and healthy JSON payload."""
    response = client.get('/health')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data is not None
    assert json_data['status'] == 'healthy'
    assert json_data['service'] == 'course-registration-app'
    assert json_data['version'] == '1.0.0'
    assert json_data['database'] == 'connected'

def test_successful_registration(client, app):
    """Test successful course registration updates seats and database records."""
    response = client.post('/register', data={
        'student_name': 'Alice Smith',
        'student_email': 'alice.smith@example.com',
        'course_id': '1'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Congratulations Alice Smith" in response.data
    assert b"Alice Smith" in response.data
    assert b"alice.smith@example.com" in response.data

    # Verify directly inside database
    with app.app_context():
        conn = get_db_connection(app.config['DATABASE'])
        reg = conn.execute(
            "SELECT * FROM registrations WHERE student_email = ?;",
            ('alice.smith@example.com',)
        ).fetchone()
        assert reg is not None
        assert reg['student_name'] == 'Alice Smith'
        assert reg['course_id'] == 1
        conn.close()

def test_duplicate_registration_rejected(client, app):
    """Test that the same email cannot register for the same course twice."""
    # First registration
    client.post('/register', data={
        'student_name': 'Bob Miller',
        'student_email': 'bob.miller@example.com',
        'course_id': '1'
    })

    # Second registration for identical course
    response = client.post('/register', data={
        'student_name': 'Bob Miller',
        'student_email': 'bob.miller@example.com',
        'course_id': '1'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Registration rejected" in response.data
    assert b"already registered" in response.data

    # Ensure exactly 1 registration exists
    with app.app_context():
        conn = get_db_connection(app.config['DATABASE'])
        count = conn.execute(
            "SELECT COUNT(*) AS total FROM registrations WHERE student_email = ?;",
            ('bob.miller@example.com',)
        ).fetchone()['total']
        assert count == 1
        conn.close()

def test_registration_rejected_when_course_full(client):
    """Test that course registrations are rejected once the seat limit is reached."""
    # Course ID 4 (K8S404) has exactly 2 seats
    # Fill seat 1
    res1 = client.post('/register', data={
        'student_name': 'Student One',
        'student_email': 'student1@example.com',
        'course_id': '4'
    }, follow_redirects=True)
    assert b"Congratulations Student One" in res1.data

    # Fill seat 2
    res2 = client.post('/register', data={
        'student_name': 'Student Two',
        'student_email': 'student2@example.com',
        'course_id': '4'
    }, follow_redirects=True)
    assert b"Congratulations Student Two" in res2.data

    # Attempt to fill seat 3 (should be rejected as course is full)
    res3 = client.post('/register', data={
        'student_name': 'Student Three',
        'student_email': 'student3@example.com',
        'course_id': '4'
    }, follow_redirects=True)
    assert res3.status_code == 200
    assert b"Registration rejected" in res3.data
    assert b"is currently full" in res3.data

def test_invalid_form_submissions(client):
    """Test validation errors for empty names, invalid email formats, and invalid course selections."""
    # 1. Missing student name
    res_no_name = client.post('/register', data={
        'student_name': '   ',
        'student_email': 'test@example.com',
        'course_id': '1'
    }, follow_redirects=True)
    assert b"Student name is required" in res_no_name.data

    # 2. Short name (< 2 characters)
    res_short_name = client.post('/register', data={
        'student_name': 'X',
        'student_email': 'test@example.com',
        'course_id': '1'
    }, follow_redirects=True)
    assert b"Student name must be at least 2 characters long" in res_short_name.data

    # 3. Invalid email format
    res_invalid_email = client.post('/register', data={
        'student_name': 'Charlie Brown',
        'student_email': 'invalid-email-format',
        'course_id': '1'
    }, follow_redirects=True)
    assert b"A valid email address is required" in res_invalid_email.data

    # 4. Non-existent course ID
    res_non_existent = client.post('/register', data={
        'student_name': 'Charlie Brown',
        'student_email': 'charlie@example.com',
        'course_id': '99999'
    }, follow_redirects=True)
    assert b"The selected course does not exist" in res_non_existent.data

    # 5. Invalid course ID format
    res_bad_id = client.post('/register', data={
        'student_name': 'Charlie Brown',
        'student_email': 'charlie@example.com',
        'course_id': 'not-a-number'
    }, follow_redirects=True)
    assert b"Please select a valid course" in res_bad_id.data

def test_registrations_page_empty_and_populated(client):
    """Test the /registrations page in empty state and after registering a student."""
    # Empty check
    res_empty = client.get('/registrations')
    assert res_empty.status_code == 200
    assert b"No Registrations Found" in res_empty.data

    # Register student
    client.post('/register', data={
        'student_name': 'Dana Scully',
        'student_email': 'dana.scully@fbi.gov',
        'course_id': '2'
    })

    # Populated check
    res_populated = client.get('/registrations')
    assert res_populated.status_code == 200
    assert b"Dana Scully" in res_populated.data
    assert b"dana.scully@fbi.gov" in res_populated.data
    assert b"PY202" in res_populated.data
