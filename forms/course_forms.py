from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from models.course import Course

CATEGORY_CHOICES = [
    ('Cloud & DevOps', 'Cloud & DevOps'),
    ('Software Engineering', 'Software Engineering'),
    ('Cybersecurity', 'Cybersecurity'),
    ('Artificial Intelligence', 'Artificial Intelligence'),
    ('Data Science & Analytics', 'Data Science & Analytics'),
    ('Computer Systems', 'Computer Systems')
]

class CourseForm(FlaskForm):
    """Course creation and editing form for Administrators."""
    code = StringField('Course Code', validators=[
        DataRequired(message="Course code is required (e.g. CS101, DEV202)."),
        Length(min=2, max=20, message="Course code must be between 2 and 20 characters.")
    ])
    title = StringField('Course Title', validators=[
        DataRequired(message="Course title is required."),
        Length(min=3, max=150, message="Title must be between 3 and 150 characters.")
    ])
    category = SelectField('Department / Category', choices=CATEGORY_CHOICES, validators=[
        DataRequired(message="Please select a course category.")
    ])
    instructor = StringField('Instructor Name', validators=[
        DataRequired(message="Instructor name is required."),
        Length(min=2, max=100, message="Instructor name must be between 2 and 100 characters.")
    ])
    credits = IntegerField('Credits', default=3, validators=[
        DataRequired(message="Course credits are required."),
        NumberRange(min=1, max=10, message="Credits must be between 1 and 10.")
    ])
    duration = StringField('Course Duration', default='12 Weeks', validators=[
        DataRequired(message="Course duration is required (e.g. 12 Weeks)."),
        Length(min=2, max=50, message="Duration must be between 2 and 50 characters.")
    ])
    capacity = IntegerField('Seat Capacity', default=30, validators=[
        DataRequired(message="Seat capacity is required."),
        NumberRange(min=1, max=500, message="Capacity must be between 1 and 500.")
    ])
    description = TextAreaField('Course Description', validators=[
        DataRequired(message="Course description is required."),
        Length(min=10, max=2000, message="Description must be between 10 and 2000 characters.")
    ])
    submit = SubmitField('Save Course')

    def __init__(self, original_course=None, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        self.original_course = original_course

    def validate_code(self, field):
        """Ensure course code is unique across all courses."""
        code_clean = field.data.strip().upper()
        existing = Course.query.filter_by(code=code_clean).first()
        if existing and (not self.original_course or existing.id != self.original_course.id):
            raise ValidationError(f"Course code '{code_clean}' already exists. Please choose a unique code.")

    def validate_capacity(self, field):
        """Enforce business rule: Capacity cannot be reduced below current enrollment count."""
        if self.original_course:
            current_enrolled = self.original_course.enrolled_count
            if field.data < current_enrolled:
                raise ValidationError(
                    f"Capacity cannot be reduced to {field.data} because {current_enrolled} students are already enrolled."
                )
