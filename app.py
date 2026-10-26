import os
from flask import Flask
from config import config_by_name
from extensions import db, login_manager, csrf
from routes import main_bp, auth_bp, courses_bp, student_bp, admin_bp, errors_bp
from services.seed_service import seed_default_data
from forms.registration_forms import EmptyForm

def create_app(config_name=None):
    """Application factory for the Course Registration Platform."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    
    # Load configuration class
    config_class = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(config_class)

    # Ensure SQLite storage directory exists
    data_dir = app.config.get('DATA_DIR')
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(errors_bp)

    # Inject global context variables for Jinja templates
    @app.context_processor
    def inject_globals():
        return {
            'app_title': 'Course Registration Platform',
            'global_logout_form': EmptyForm(),
            'current_year': 2026
        }

    # Initialize database tables and seed sample data idempotently
    with app.app_context():
        db.create_all()
        # Seed default accounts and course catalog if not in isolated unit tests
        if not app.config.get('TESTING'):
            seed_default_data()

    return app

# Application instance for Gunicorn WSGI and local execution
app = create_app()

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"Starting Course Registration Platform on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
