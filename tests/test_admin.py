from extensions import db
from models.course import Course
from models.registration import Registration
from models.user import User

def test_admin_dashboard_renders_kpis(admin_client):
    """Test admin dashboard renders system stats and tables."""
    res = admin_client.get('/admin/dashboard')
    assert res.status_code == 200
    assert b"Administrator Control Center" in res.data
    assert b"Total Courses" in res.data

def test_admin_can_create_new_course(admin_client, app):
    """Test administrator can create a new course."""
    res = admin_client.post('/admin/courses/new', data={
        'code': 'SEC401',
        'title': 'Applied Cryptography',
        'category': 'Cybersecurity',
        'instructor': 'Dr. Rivest',
        'credits': 4,
        'duration': '14 Weeks',
        'capacity': 25,
        'description': 'Modern public-key cryptography, TLS architectures, and secure hash functions.'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"created successfully" in res.data

    with app.app_context():
        course = Course.query.filter_by(code='SEC401').first()
        assert course is not None
        assert course.capacity == 25

def test_admin_capacity_cannot_be_reduced_below_enrolled_count(admin_client, student_client, student2_client, app):
    """Test business rule: Course capacity cannot be set lower than active student enrollment."""
    # Enroll two students in Course 1
    student_client.post('/courses/1/register', follow_redirects=True)
    student2_client.post('/courses/1/register', follow_redirects=True)

    with app.app_context():
        c1 = db.session.get(Course, 1)
        assert c1.enrolled_count == 2

    # Attempt to edit Course 1 with capacity = 1 (less than enrolled count of 2)
    res = admin_client.post('/admin/courses/1/edit', data={
        'code': 'CS101',
        'title': 'Intro to Computer Science',
        'category': 'Computer Science',
        'instructor': 'Prof. Turing',
        'credits': 3,
        'duration': '12 Weeks',
        'capacity': 1,  # Invalid: less than enrolled count of 2
        'description': 'Foundational computer science principles and algorithms.'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Capacity cannot be reduced to 1 because 2 students are already enrolled" in res.data

def test_admin_cannot_delete_course_with_active_enrollments(admin_client, student_client, app):
    """Test that deleting a course with active enrollments is blocked."""
    # Enroll student in Course 1
    student_client.post('/courses/1/register', follow_redirects=True)

    # Attempt to delete Course 1
    del_res = admin_client.post('/admin/courses/1/delete', follow_redirects=True)
    assert del_res.status_code == 200
    assert b"Cannot delete course" in del_res.data
    assert b"active student enrollments" in del_res.data

    # Verify course still exists
    with app.app_context():
        assert Course.query.get(1) is not None

def test_admin_can_delete_course_without_enrollments(admin_client, app):
    """Test that a course with zero enrollments can be deleted."""
    del_res = admin_client.post('/admin/courses/2/delete', follow_redirects=True)
    assert del_res.status_code == 200
    assert b"has been permanently removed" in del_res.data

    with app.app_context():
        assert Course.query.get(2) is None

def test_admin_registrations_view_shows_records(admin_client, student_client):
    """Test that admin registrations log displays student enrollments."""
    # Enroll student in Course 1
    student_client.post('/courses/1/register', follow_redirects=True)

    res = admin_client.get('/admin/registrations')
    assert res.status_code == 200
    assert b"Alice Student" in res.data
    assert b"alice@test.edu" in res.data
    assert b"CS101" in res.data
