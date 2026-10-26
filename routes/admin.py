from flask import Blueprint, render_template, redirect, url_for, flash, request
from extensions import db
from models.user import User
from models.course import Course
from models.registration import Registration
from forms.course_forms import CourseForm
from forms.registration_forms import EmptyForm
from utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Administrator control center with system metrics and registration telemetry."""
    total_courses = Course.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_enrollments = Registration.query.filter_by(status='ENROLLED').count()
    
    total_capacity = db.session.query(db.func.sum(Course.capacity)).scalar() or 0
    utilization_rate = int((total_enrollments / total_capacity * 100)) if total_capacity > 0 else 0

    recent_registrations = Registration.query.order_by(Registration.registered_at.desc()).limit(8).all()
    courses = Course.query.order_by(Course.code.asc()).all()

    return render_template(
        'admin/dashboard.html',
        total_courses=total_courses,
        total_students=total_students,
        total_enrollments=total_enrollments,
        total_capacity=total_capacity,
        utilization_rate=utilization_rate,
        recent_registrations=recent_registrations,
        courses=courses
    )

@admin_bp.route('/courses')
@admin_required
def courses():
    """Master course inventory and management interface."""
    all_courses = Course.query.order_by(Course.code.asc()).all()
    delete_form = EmptyForm()
    return render_template('admin/courses.html', courses=all_courses, delete_form=delete_form)

@admin_bp.route('/courses/new', methods=['GET', 'POST'])
@admin_required
def create_course():
    """Create a new academic course offering with validation."""
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            code=form.code.data.strip().upper(),
            title=form.title.data.strip(),
            category=form.category.data,
            instructor=form.instructor.data.strip(),
            credits=form.credits.data,
            duration=form.duration.data.strip(),
            capacity=form.capacity.data,
            description=form.description.data.strip()
        )
        db.session.add(course)
        db.session.commit()
        flash(f"Course '{course.code} - {course.title}' created successfully.", "success")
        return redirect(url_for('admin.courses'))

    return render_template('admin/course_form.html', form=form, title="Create New Course")

@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_course(course_id):
    """Edit an existing course while enforcing capacity constraint rules."""
    course = Course.query.get_or_404(course_id)
    form = CourseForm(original_course=course)

    if form.validate_on_submit():
        course.code = form.code.data.strip().upper()
        course.title = form.title.data.strip()
        course.category = form.category.data
        course.instructor = form.instructor.data.strip()
        course.credits = form.credits.data
        course.duration = form.duration.data.strip()
        course.capacity = form.capacity.data
        course.description = form.description.data.strip()

        db.session.commit()
        flash(f"Course '{course.code}' updated successfully.", "success")
        return redirect(url_for('admin.courses'))

    if request.method == 'GET':
        form.code.data = course.code
        form.title.data = course.title
        form.category.data = course.category
        form.instructor.data = course.instructor
        form.credits.data = course.credits
        form.duration.data = course.duration
        form.capacity.data = course.capacity
        form.description.data = course.description

    return render_template(
        'admin/course_form.html',
        form=form,
        course=course,
        title=f"Edit Course: {course.code}"
    )

@admin_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@admin_required
def delete_course(course_id):
    """Delete a course only if it has no active student enrollments."""
    form = EmptyForm()
    if not form.validate_on_submit():
        flash("Invalid security token.", "danger")
        return redirect(url_for('admin.courses'))

    course = Course.query.get_or_404(course_id)

    # Enforce business rule: Prevent deleting courses with active enrollments
    if course.enrolled_count > 0:
        flash(f"Cannot delete course '{course.code}': There are {course.enrolled_count} active student enrollments. Please drop or cancel enrollments first.", "danger")
        return redirect(url_for('admin.courses'))

    db.session.delete(course)
    db.session.commit()
    flash(f"Course '{course.code}' has been permanently removed.", "info")
    return redirect(url_for('admin.courses'))

@admin_bp.route('/registrations')
@admin_required
def registrations():
    """Master audit log of all student registrations with search and filtering."""
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Registration.query.join(User, Registration.student_id == User.id).join(Course, Registration.course_id == Course.id)

    if search_query:
        like_pattern = f"%{search_query}%"
        query = query.filter(
            (User.name.ilike(like_pattern)) |
            (User.email.ilike(like_pattern)) |
            (Course.code.ilike(like_pattern)) |
            (Course.title.ilike(like_pattern))
        )

    if status_filter:
        query = query.filter(Registration.status == status_filter)

    all_regs = query.order_by(Registration.registered_at.desc()).all()

    return render_template(
        'admin/registrations.html',
        registrations=all_regs,
        search_query=search_query,
        selected_status=status_filter
    )
