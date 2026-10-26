from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models.user import User
from forms.auth_forms import LoginForm, RegisterForm, ProfileForm, ChangePasswordForm
from forms.registration_forms import EmptyForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Authenticates students and administrators."""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        email_clean = form.email.data.strip().lower()
        user = User.query.filter_by(email=email_clean).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back, {user.name}!", "success")
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('student.dashboard'))
        else:
            flash("Invalid email or password. Please check your credentials.", "danger")

    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registers a new student account."""
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            role='student'
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Registration successful! Welcome to the Course Registration Platform.", "success")
        return redirect(url_for('student.dashboard'))

    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logs out the authenticated user."""
    logout_user()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management and password change."""
    profile_form = ProfileForm(prefix='profile')
    password_form = ChangePasswordForm(prefix='password')
    logout_form = EmptyForm()

    if 'profile-submit' in request.form and profile_form.validate_on_submit():
        current_user.name = profile_form.name.data.strip()
        db.session.commit()
        flash("Your profile information has been updated successfully.", "success")
        return redirect(url_for('auth.profile'))

    if 'password-submit' in request.form and password_form.validate_on_submit():
        if not current_user.check_password(password_form.current_password.data):
            flash("Incorrect current password.", "danger")
        else:
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash("Your password has been changed successfully.", "success")
            return redirect(url_for('auth.profile'))

    if request.method == 'GET':
        profile_form.name.data = current_user.name

    return render_template(
        'auth/profile.html',
        profile_form=profile_form,
        password_form=password_form,
        logout_form=logout_form
    )
