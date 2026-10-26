from datetime import datetime, timezone
from extensions import db

class Course(db.Model):
    """Academic course offering model."""
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(60), nullable=False, default='Computer Science')
    instructor = db.Column(db.String(100), nullable=False)
    credits = db.Column(db.Integer, nullable=False, default=3)
    duration = db.Column(db.String(50), nullable=False, default='12 Weeks')
    capacity = db.Column(db.Integer, nullable=False, default=30)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    registrations = db.relationship(
        'Registration',
        back_populates='course',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    @property
    def enrolled_count(self):
        """Calculates current active enrollments from SQLite database."""
        # Query registrations where status is ENROLLED
        from models.registration import Registration
        return Registration.query.filter_by(course_id=self.id, status='ENROLLED').count()

    @property
    def available_seats(self):
        """Calculates remaining available seats."""
        return max(0, self.capacity - self.enrolled_count)

    @property
    def is_full(self):
        """Returns True if no seats remain."""
        return self.available_seats <= 0

    @property
    def enrollment_percentage(self):
        """Returns integer percentage of seats filled (0-100)."""
        if self.capacity <= 0:
            return 100
        return min(100, int((self.enrolled_count / self.capacity) * 100))

    def __repr__(self):
        return f"<Course id={self.id} code='{self.code}' title='{self.title}'>"
