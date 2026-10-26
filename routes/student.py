from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models.course import Course
from models.registration import Registration
from forms.registration_forms import EmptyForm

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
def dashboard():
    """Student dashboard providing real database-backed metrics and enrolled courses."""
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    active_registrations = Registration.query.filter_by(
        student_id=current_user.id,
        status='ENROLLED'
    ).order_by(Registration.registered_at.desc()).all()

    total_available_courses = Course.query.count()
    
    # Calculate total remaining open seats across all university courses
    all_courses = Course.query.all()
    total_remaining_seats = sum(c.available_seats for c in all_courses)
    total_credits = sum(r.course.credits for r in active_registrations)

    form = EmptyForm()

    return render_template(
        'student/dashboard.html',
        active_registrations=active_registrations,
        total_available_courses=total_available_courses,
        total_remaining_seats=total_remaining_seats,
        total_credits=total_credits,
        form=form
    )

@student_bp.route('/my-registrations')
@login_required
def my_registrations():
    """Student registration management page showing enrolled courses and cancellation options."""
    if current_user.is_admin():
        return redirect(url_for('admin.registrations'))

    registrations = Registration.query.filter_by(
        student_id=current_user.id
    ).order_by(Registration.registered_at.desc()).all()

    form = EmptyForm()

    return render_template(
        'student/my_registrations.html',
        registrations=registrations,
        form=form
    )

@student_bp.route('/my-registrations/<int:reg_id>/cancel', methods=['POST'])
@login_required
def cancel_registration(reg_id):
    """Cancels an enrollment and immediately releases the reserved seat."""
    form = EmptyForm()
    if not form.validate_on_submit():
        flash("Invalid security token. Please try again.", "danger")
        return redirect(url_for('student.my_registrations'))

    registration = Registration.query.get_or_404(reg_id)

    # Enforce security authorization: Students can only cancel their own registrations
    if registration.student_id != current_user.id and not current_user.is_admin():
        flash("Unauthorized action: You cannot modify another student's registration.", "danger")
        abort(403)

    course_title = registration.course.title
    course_code = registration.course.code

    # Set status to CANCELLED to release the seat calculation
    registration.status = 'CANCELLED'
    db.session.commit()

    flash(f"Your enrollment in '{course_code} - {course_title}' has been successfully cancelled and the seat released.", "info")
    return redirect(url_for('student.my_registrations'))
