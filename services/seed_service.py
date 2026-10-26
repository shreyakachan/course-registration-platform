from extensions import db
from models.user import User
from models.course import Course
from models.registration import Registration

DEFAULT_COURSES = [
    {
        'code': 'DEV101',
        'title': 'Cloud & DevOps Engineering',
        'category': 'Cloud & DevOps',
        'description': 'Master modern Continuous Integration and Continuous Deployment (CI/CD) pipelines, Docker containerization, Infrastructure as Code, and production telemetry.',
        'instructor': 'Prof. Sarah Jenkins',
        'credits': 4,
        'duration': '14 Weeks',
        'capacity': 30
    },
    {
        'code': 'PY202',
        'title': 'Full-Stack Python & Flask Architecture',
        'category': 'Software Engineering',
        'description': 'Build scalable, secure web applications, RESTful microservices, and database-driven dynamic services using Flask, SQLAlchemy ORM, and Bootstrap 5.',
        'instructor': 'Dr. Alan Pyke',
        'credits': 3,
        'duration': '12 Weeks',
        'capacity': 25
    },
    {
        'code': 'SEC303',
        'title': 'DevSecOps & Cloud Application Security',
        'category': 'Cybersecurity',
        'description': 'Implement automated vulnerability scanning, container security audits, secrets rotation, and security gate enforcement in modern software delivery pipelines.',
        'instructor': 'Dr. Maya Lin',
        'credits': 3,
        'duration': '10 Weeks',
        'capacity': 20
    },
    {
        'code': 'AI405',
        'title': 'Applied Machine Learning & Neural Systems',
        'category': 'Artificial Intelligence',
        'description': 'Hands-on deep learning workflows, model serving via APIs, feature engineering, and monitoring machine learning systems in production cloud environments.',
        'instructor': 'Dr. Marcus Thorne',
        'credits': 4,
        'duration': '14 Weeks',
        'capacity': 20
    },
    {
        'code': 'K8S404',
        'title': 'Advanced Kubernetes Cluster Administration',
        'category': 'Cloud & DevOps',
        'description': 'Container orchestration at scale: custom resource definitions, ingress controllers, pod disruption budgets, service meshes, and rolling zero-downtime updates.',
        'instructor': 'Prof. David Vance',
        'credits': 3,
        'duration': '10 Weeks',
        'capacity': 2  # Configured to 2 seats to facilitate easy demonstration of seat limits
    }
]

def seed_default_data():
    """Seeds the SQLite database idempotently with initial accounts and course catalog."""
    # 1. Seed Administrator Account
    admin = User.query.filter_by(email='admin@university.edu').first()
    if not admin:
        admin = User(
            name='System Administrator',
            email='admin@university.edu',
            role='admin'
        )
        admin.set_password('Admin123!')
        db.session.add(admin)

    # 2. Seed Default Student Account
    student = User.query.filter_by(email='student@university.edu').first()
    if not student:
        student = User(
            name='Vaishnavi Kedar',
            email='student@university.edu',
            role='student'
        )
        student.set_password('Student123!')
        db.session.add(student)

    db.session.commit()

    # 3. Seed Course Catalog
    for course_data in DEFAULT_COURSES:
        course = Course.query.filter_by(code=course_data['code']).first()
        if not course:
            course = Course(**course_data)
            db.session.add(course)

    db.session.commit()

    # 4. Seed an initial registration for the default student if none exist
    dev101 = Course.query.filter_by(code='DEV101').first()
    if dev101 and student:
        existing_reg = Registration.query.filter_by(
            student_id=student.id,
            course_id=dev101.id
        ).first()
        if not existing_reg:
            initial_reg = Registration(
                student_id=student.id,
                course_id=dev101.id,
                status='ENROLLED'
            )
            db.session.add(initial_reg)
            db.session.commit()
