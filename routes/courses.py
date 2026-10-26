from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models.course import Course
from models.registration import Registration
from forms.registration_forms import EmptyForm

courses_bp = Blueprint('courses', __name__, url_prefix='/courses')

@courses_bp.route('/')
def catalog():
    """Browse course catalog with search, department filtering, and sorting."""
    search_query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    sort_by = request.args.get('sort', 'code').strip()

    query = Course.query

    if search_query:
        like_pattern = f"%{search_query}%"
        query = query.filter(
            (Course.code.ilike(like_pattern)) |
            (Course.title.ilike(like_pattern)) |
            (Course.instructor.ilike(like_pattern)) |
            (Course.description.ilike(like_pattern))
        )

    if category_filter:
        query = query.filter_by(category=category_filter)

    if sort_by == 'title':
        query = query.order_by(Course.title.asc())
    elif sort_by == 'credits':
        query = query.order_by(Course.credits.desc())
    elif sort_by == 'capacity':
        query = query.order_by(Course.capacity.desc())
    else:  # default by course code
        query = query.order_by(Course.code.asc())

    courses = query.all()

    # Get distinct departments for filter dropdown
    categories = [r[0] for r in db.session.query(Course.category).distinct().order_by(Course.category).all()]

    # Collect IDs of courses the current user is enrolled in
    user_enrolled_course_ids = set()
    if current_user.is_authenticated and current_user.is_student():
        active_regs = Registration.query.filter_by(
            student_id=current_user.id,
            status='ENROLLED'
        ).all()
        user_enrolled_course_ids = {r.course_id for r in active_regs}

    return render_template(
        'courses/catalog.html',
        courses=courses,
        categories=categories,
        search_query=search_query,
        selected_category=category_filter,
        sort_by=sort_by,
        user_enrolled_course_ids=user_enrolled_course_ids
    )

@courses_bp.route('/<int:course_id>')
def detail(course_id):
    """Course detail page with instructor biography, syllabus details, and enrollment status."""
    course = Course.query.get_or_404(course_id)
    form = EmptyForm()

    is_enrolled = False
    if current_user.is_authenticated and current_user.is_student():
        active_reg = Registration.query.filter_by(
            student_id=current_user.id,
            course_id=course.id,
            status='ENROLLED'
        ).first()
        is_enrolled = bool(active_reg)

    return render_template(
        'courses/detail.html',
        course=course,
        is_enrolled=is_enrolled,
        form=form
    )

@courses_bp.route('/<int:course_id>/register', methods=['POST'])
@login_required
def register_course(course_id):
    """Handles course registration with atomic seat and duplicate validation."""
    if current_user.is_admin():
        flash("Administrators cannot register for student courses.", "info")
        return redirect(url_for('courses.detail', course_id=course_id))

    form = EmptyForm()
    if not form.validate_on_submit():
        flash("Invalid security token. Please try again.", "danger")
        return redirect(url_for('courses.detail', course_id=course_id))

    course = Course.query.get_or_404(course_id)

    # 1. Enforce business rule: Prevent duplicate active registration
    existing_reg = Registration.query.filter_by(
        student_id=current_user.id,
        course_id=course.id,
        status='ENROLLED'
    ).first()

    if existing_reg:
        flash(f"You are already actively enrolled in '{course.code} - {course.title}'.", "warning")
        return redirect(url_for('courses.detail', course_id=course_id))

    # 2. Enforce business rule: Prevent registration if course is full
    if course.is_full:
        flash(f"Enrollment rejected: Course '{course.code}' has reached its maximum capacity of {course.capacity} seats.", "danger")
        return redirect(url_for('courses.detail', course_id=course_id))

    # 3. Create or re-activate enrollment
    past_cancelled_reg = Registration.query.filter_by(
        student_id=current_user.id,
        course_id=course.id,
        status='CANCELLED'
    ).first()

    if past_cancelled_reg:
        past_cancelled_reg.status = 'ENROLLED'
    else:
        new_reg = Registration(
            student_id=current_user.id,
            course_id=course.id,
            status='ENROLLED'
        )
        db.session.add(new_reg)

    db.session.commit()
    flash(f"Success! You have officially enrolled in '{course.code} - {course.title}'.", "success")
    return redirect(url_for('student.my_registrations'))
