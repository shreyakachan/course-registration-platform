from models.course import Course
from models.registration import Registration
from models.user import User
from extensions import db

def test_successful_course_registration(student_client, app):
    """Test that an authenticated student can enroll in an open course."""
    res = student_client.post('/courses/1/register', follow_redirects=True)
    assert res.status_code == 200
    assert b"Success! You have officially enrolled" in res.data
    assert b"CS101" in res.data

    # Verify registration in database
    with app.app_context():
        course = Course.query.get(1)
        assert course.enrolled_count == 1
        assert course.available_seats == 9

def test_duplicate_registration_rejected(student_client):
    """Test that a student cannot enroll twice in the same course."""
    # First enrollment
    student_client.post('/courses/1/register', follow_redirects=True)

    # Second enrollment attempt
    res = student_client.post('/courses/1/register', follow_redirects=True)
    assert res.status_code == 200
    assert b"already actively enrolled" in res.data

def test_registration_rejected_when_course_full(student_client, student2_client, app):
    """Test that enrollment is rejected once a course hits capacity limit."""
    # Course 2 (K8S101) has capacity=1
    # Student 1 fills the only seat
    res1 = student_client.post('/courses/2/register', follow_redirects=True)
    assert res1.status_code == 200
    assert b"Success! You have officially enrolled" in res1.data

    # Verify course is now full
    with app.app_context():
        course = Course.query.get(2)
        assert course.is_full is True
        assert course.available_seats == 0

    # Student 2 attempts to register for the full course
    res2 = student2_client.post('/courses/2/register', follow_redirects=True)
    assert res2.status_code == 200
    assert b"reached its maximum capacity" in res2.data

def test_cancellation_releases_seat(student_client, student2_client, app):
    """Test that dropping a course restores the available seat count."""
    # Student 1 fills seat in Course 2 (capacity=1)
    student_client.post('/courses/2/register', follow_redirects=True)

    with app.app_context():
        alice = User.query.filter_by(email='alice@test.edu').first()
        reg = Registration.query.filter_by(student_id=alice.id, course_id=2, status='ENROLLED').first()
        reg_id = reg.id

    # Student 1 cancels the registration
    cancel_res = student_client.post(f'/my-registrations/{reg_id}/cancel', follow_redirects=True)
    assert cancel_res.status_code == 200
    assert b"has been successfully cancelled and the seat released" in cancel_res.data

    # Verify seat is freed
    with app.app_context():
        course = Course.query.get(2)
        assert course.available_seats == 1
        assert course.is_full is False

    # Now Student 2 can successfully take the released seat
    res2 = student2_client.post('/courses/2/register', follow_redirects=True)
    assert res2.status_code == 200
    assert b"Success! You have officially enrolled" in res2.data

def test_unauthorized_cancellation_rejected(student_client, student2_client, app):
    """Test that a student cannot cancel another student's registration."""
    # Student 1 registers for Course 1
    student_client.post('/courses/1/register', follow_redirects=True)

    with app.app_context():
        alice = User.query.filter_by(email='alice@test.edu').first()
        reg = Registration.query.filter_by(student_id=alice.id, course_id=1, status='ENROLLED').first()
        reg_id = reg.id

    # Student 2 attempts to cancel Student 1's registration
    unauthorized_res = student2_client.post(f'/my-registrations/{reg_id}/cancel')
    assert unauthorized_res.status_code == 403
    assert b"Access Forbidden" in unauthorized_res.data

    # Ensure Student 1 is still enrolled
    with app.app_context():
        reg_check = Registration.query.get(reg_id)
        assert reg_check.status == 'ENROLLED'
