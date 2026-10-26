from flask_wtf import FlaskForm
from wtforms import SubmitField

class EmptyForm(FlaskForm):
    """Empty form used exclusively for CSRF protection on POST actions."""
    submit = SubmitField('Submit')
