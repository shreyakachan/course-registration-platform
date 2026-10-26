import pytest
from unittest.mock import patch
from extensions import db

def test_home_page_renders_successfully(client):
    """Test that the home page returns HTTP 200 and displays platform metrics."""
    res = client.get('/')
    assert res.status_code == 200
    assert b"Course Registration Portal" in res.data
    assert b"CS101" in res.data
    assert b"Intro to Computer Science" in res.data

def test_health_endpoint_healthy(client):
    """Test that /health returns HTTP 200 and healthy JSON payload with database status."""
    res = client.get('/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data is not None
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'
    assert data['service'] == 'course-registration-platform'
    assert data['active_courses'] >= 2

def test_health_endpoint_reports_unhealthy_when_database_fails(client):
    """Test that /health returns HTTP 500 when database connectivity is disrupted."""
    with patch.object(db.session, 'execute', side_effect=Exception("Database connection timeout")):
        res = client.get('/health')
        assert res.status_code == 500
        data = res.get_json()
        assert data['status'] == 'unhealthy'
        assert "Database connection timeout" in data['error']
