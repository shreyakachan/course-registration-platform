def test_course_catalog_renders_courses(client):
    """Test that course catalog displays all active courses."""
    res = client.get('/courses/')
    assert res.status_code == 200
    assert b"CS101" in res.data
    assert b"K8S101" in res.data
    assert b"Container Engineering" in res.data

def test_course_catalog_search_and_filter(client):
    """Test filtering courses by keyword and department."""
    # Search for 'Container'
    search_res = client.get('/courses/?q=Container')
    assert search_res.status_code == 200
    assert b"K8S101" in search_res.data
    assert b"CS101" not in search_res.data

    # Filter by category
    filter_res = client.get('/courses/?category=Cloud+%26+DevOps')
    assert filter_res.status_code == 200
    assert b"K8S101" in filter_res.data
    assert b"CS101" not in filter_res.data

def test_course_detail_page_renders_accurately(client):
    """Test course details page shows syllabus, credits, and instructor."""
    res = client.get('/courses/1')
    assert res.status_code == 200
    assert b"CS101" in res.data
    assert b"Prof. Turing" in res.data
    assert b"3 Credits" in res.data

def test_nonexistent_course_returns_404(client):
    """Test requesting invalid course ID produces clean 404 error page."""
    res = client.get('/courses/9999')
    assert res.status_code == 404
    assert b"Page Not Found" in res.data
