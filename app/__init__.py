"""Flask application factory"""
from flask import Flask, render_template, redirect, url_for
from app.config import Config


def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)
    
    # Initialize extensions here (database, login manager, etc.)
    # TODO: Add extensions as needed
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Add template context processors
    @app.context_processor
    def inject_config():
        """Make config available in templates"""
        return dict(
            config=app.config
        )
    
    # Home route
    @app.route('/')
    def index():
        return redirect(url_for('admin.dashboard'))
    
    return app

def register_blueprints(app):
    """Register all blueprints"""
    
    # Core blueprints (always registered)
    try:
        from app.auth.routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
    except ImportError:
        print("Warning: Auth blueprint not found")
    
    try:
        from app.admin.routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
    except ImportError:
        print("Warning: Admin blueprint not found")
    
    try:
        from app.tutor.routes import tutor_bp
        app.register_blueprint(tutor_bp, url_prefix='/tutor')
    except ImportError:
        print("Warning: Tutor blueprint not found")
    
    try:
        from app.api.routes import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
    except ImportError:
        print("Warning: API blueprint not found")
    


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
