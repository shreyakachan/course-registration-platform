"""End-to-End integration tests for Course Registration Platform."""

def test_full_student_journey(client, app):
    """Test full journey: registration, login, catalog browse, enrollment, and dashboard verification."""
    # 1. Register student
    reg_res = client.post('/register', data={
        'name': 'David Miller',
        'email': 'david@test.edu',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }, follow_redirects=True)
    assert reg_res.status_code == 200
    assert b"Student Dashboard" in reg_res.data

    # 2. Browse catalog
    catalog_res = client.get('/courses/')
    assert catalog_res.status_code == 200
    assert b"CS101" in catalog_res.data

    # 3. View detail
    detail_res = client.get('/courses/1')
    assert detail_res.status_code == 200
    assert b"Confirm &amp; Enroll Now" in detail_res.data

    # 4. Enroll
    enroll_res = client.post('/courses/1/register', follow_redirects=True)
    assert enroll_res.status_code == 200
    assert b"Success! You have officially enrolled" in enroll_res.data

    # 5. Verify on My Enrollments
    my_regs_res = client.get('/my-registrations')
    assert my_regs_res.status_code == 200
    assert b"CS101" in my_regs_res.data
    assert b"Active" in my_regs_res.data
