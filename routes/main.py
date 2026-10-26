from flask import Blueprint, render_template, jsonify
from extensions import db
from models.course import Course
from models.user import User
from models.registration import Registration

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Platform landing page with live database metrics and featured courses."""
    total_courses = Course.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_enrollments = Registration.query.filter_by(status='ENROLLED').count()
    total_capacity = db.session.query(db.func.sum(Course.capacity)).scalar() or 0
    total_available_seats = max(0, total_capacity - total_enrollments)

    featured_courses = Course.query.order_by(Course.id.asc()).limit(3).all()

    return render_template(
        'index.html',
        total_courses=total_courses,
        total_students=total_students,
        total_enrollments=total_enrollments,
        total_available_seats=total_available_seats,
        featured_courses=featured_courses
    )

@main_bp.route('/health')
def health():
    """Health verification endpoint for Docker, Jenkins, and uptime probes."""
    try:
        # Verify active database connectivity
        db.session.execute(db.text("SELECT 1;")).fetchone()
        course_count = Course.query.count()
        return jsonify({
            "status": "healthy",
            "service": "course-registration-platform",
            "version": "2.0.0",
            "database": "connected",
            "active_courses": course_count
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "service": "course-registration-platform",
            "error": str(e)
        }), 500
