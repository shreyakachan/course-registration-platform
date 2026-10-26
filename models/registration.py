from datetime import datetime, timezone
from extensions import db

class Registration(db.Model):
    """Course enrollment record linking students and courses."""
    __tablename__ = 'registrations'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='ENROLLED')  # 'ENROLLED', 'CANCELLED'
    registered_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Unique constraint enforcing only one registration per student/course combination
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='uq_student_course'),
    )

    # Relationships
    student = db.relationship('User', back_populates='registrations')
    course = db.relationship('Course', back_populates='registrations')

    def cancel(self):
        """Marks enrollment as cancelled."""
        self.status = 'CANCELLED'

    def is_active(self):
        """Returns True if the enrollment is currently active."""
        return self.status == 'ENROLLED'

    def __repr__(self):
        return f"<Registration id={self.id} student_id={self.student_id} course_id={self.course_id} status='{self.status}'>"
