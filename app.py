import os
import re
import sqlite3
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    g
)

SAMPLE_COURSES = [
    (
        'DEV101',
        'Cloud & DevOps Fundamentals',
        'Master Git version control, CI/CD pipelines, Docker containerization, and modern cloud deployment architectures.',
        'Prof. Sarah Jenkins',
        30
    ),
    (
        'PY202',
        'Full-Stack Python & Flask',
        'Build scalable web applications, RESTful APIs, and database-driven services using Python, Flask, and SQLite.',
        'Dr. Alan Pyke',
        25
    ),
    (
        'SEC303',
        'DevSecOps & Application Security',
        'Learn automated security scanning, container vulnerability audits, secrets handling, and secure software delivery.',
        'Dr. Maya Lin',
        20
    ),
    (
        'K8S404',
        'Kubernetes Cluster Administration',
        'Production container orchestration, service meshes, helm charts, pod autoscaling, and zero-downtime rollouts.',
        'Prof. David Vance',
        2  # Set to 2 seats to facilitate easy demonstration of seat limits
    )
]

def get_db_connection(db_path):
    """Establishes a connection to the SQLite database with row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path):
    """Initializes tables and seeds sample courses if not already present."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            instructor TEXT NOT NULL,
            total_seats INTEGER NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            student_email TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
            UNIQUE(course_id, student_email)
        );
    """)

    # Seed initial courses if empty
    cursor.execute("SELECT COUNT(*) AS count FROM courses;")
    count = cursor.fetchone()['count']
    if count == 0:
        cursor.executemany("""
            INSERT INTO courses (code, title, description, instructor, total_seats)
            VALUES (?, ?, ?, ?, ?);
        """, SAMPLE_COURSES)
        conn.commit()

    conn.close()

def create_app(test_config=None):
    """Application factory for Course Registration Web App."""
    app = Flask(__name__, instance_relative_config=True)

    default_data_dir = os.environ.get('DATA_DIR', os.path.join(app.root_path, 'data'))
    default_db_path = os.path.join(default_data_dir, 'course_app.db')

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-course-app-2026'),
        DATABASE=default_db_path,
    )

    if test_config:
        app.config.update(test_config)

    # Initialize the database
    with app.app_context():
        init_db(app.config['DATABASE'])

    def get_db():
        if 'db' not in g:
            g.db = get_db_connection(app.config['DATABASE'])
        return g.db

    @app.teardown_appcontext
    def close_db(error=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    def fetch_courses():
        """Retrieve all courses along with registration count and remaining seats."""
        db = get_db()
        query = """
            SELECT c.id, c.code, c.title, c.description, c.instructor, c.total_seats,
                   COUNT(r.id) AS registered_count,
                   (c.total_seats - COUNT(r.id)) AS available_seats
            FROM courses c
            LEFT JOIN registrations r ON c.id = r.course_id
            GROUP BY c.id
            ORDER BY c.id ASC;
        """
        return db.execute(query).fetchall()

    def fetch_course_by_id(course_id):
        """Retrieve a single course with seat availability."""
        db = get_db()
        query = """
            SELECT c.id, c.code, c.title, c.description, c.instructor, c.total_seats,
                   COUNT(r.id) AS registered_count,
                   (c.total_seats - COUNT(r.id)) AS available_seats
            FROM courses c
            LEFT JOIN registrations r ON c.id = r.course_id
            WHERE c.id = ?
            GROUP BY c.id;
        """
        return db.execute(query, (course_id,)).fetchone()

    @app.route('/')
    def index():
        """Home page: Displays available courses and registration form."""
        courses = fetch_courses()
        return render_template('index.html', courses=courses)

    @app.route('/register', methods=['POST'])
    def register():
        """Handles course registration with validation and constraint enforcement."""
        student_name = request.form.get('student_name', '').strip()
        student_email = request.form.get('student_email', '').strip().lower()
        course_id_raw = request.form.get('course_id', '').strip()

        # 1. Field validation
        if not student_name:
            flash("Student name is required.", "danger")
            return redirect(url_for('index'))

        if len(student_name) < 2:
            flash("Student name must be at least 2 characters long.", "danger")
            return redirect(url_for('index'))

        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not student_email or not re.match(email_regex, student_email):
            flash("A valid email address is required (e.g., student@example.com).", "danger")
            return redirect(url_for('index'))

        if not course_id_raw or not course_id_raw.isdigit():
            flash("Please select a valid course.", "danger")
            return redirect(url_for('index'))

        course_id = int(course_id_raw)
        course = fetch_course_by_id(course_id)

        if not course:
            flash("The selected course does not exist.", "danger")
            return redirect(url_for('index'))

        # 2. Seat limit check
        if course['available_seats'] <= 0:
            flash(f"Registration rejected: Course '{course['title']}' is currently full ({course['total_seats']}/{course['total_seats']} seats taken).", "danger")
            return redirect(url_for('index'))

        # 3. Duplicate registration check
        db = get_db()
        existing = db.execute(
            "SELECT id FROM registrations WHERE course_id = ? AND student_email = ?;",
            (course_id, student_email)
        ).fetchone()

        if existing:
            flash(f"Registration rejected: Email '{student_email}' is already registered for '{course['title']}'.", "warning")
            return redirect(url_for('index'))

        # 4. Insert registration
        try:
            db.execute(
                "INSERT INTO registrations (course_id, student_name, student_email) VALUES (?, ?, ?);",
                (course_id, student_name, student_email)
            )
            db.commit()
            flash(f"Congratulations {student_name}! Successfully enrolled in '{course['title']}'.", "success")
            return redirect(url_for('registrations'))
        except sqlite3.IntegrityError:
            flash("Registration could not be completed due to a database conflict.", "danger")
            return redirect(url_for('index'))

    @app.route('/registrations')
    def registrations():
        """Displays the list of enrolled students and their assigned courses."""
        db = get_db()
        query = """
            SELECT r.id, r.student_name, r.student_email, r.registered_at,
                   c.code AS course_code, c.title AS course_title
            FROM registrations r
            JOIN courses c ON r.course_id = c.id
            ORDER BY r.id DESC;
        """
        rows = db.execute(query).fetchall()
        return render_template('registrations.html', registrations=rows)

    @app.route('/health')
    def health():
        """Health check endpoint for Docker and Jenkins CI/CD pipeline verification."""
        try:
            db = get_db()
            db.execute("SELECT 1;").fetchone()
            return jsonify({
                "status": "healthy",
                "service": "course-registration-app",
                "version": "1.0.0",
                "database": "connected"
            }), 200
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "service": "course-registration-app",
                "error": str(e)
            }), 500

    return app

app = create_app()

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"Starting Course Registration Web App on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
