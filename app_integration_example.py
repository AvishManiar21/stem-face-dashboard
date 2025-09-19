"""
Example of how to integrate the group system into your existing app.py
This shows the minimal changes needed to add user grouping and permission control
"""

# Add these imports to your existing app.py
from flask_sqlalchemy import SQLAlchemy
from models import db, Group, GroupMember, Permission, GroupPermission, User
from group_routes import group_bp
from group_helpers import initialize_group_system, get_user_all_permissions, get_user_groups

# Add this to your existing Flask app initialization
def create_app():
    app = Flask(__name__)
    
    # Your existing configuration
    app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Add database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///group_system.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Register the group blueprint
    app.register_blueprint(group_bp)
    
    # Your existing routes...
    
    return app

# Add this before_request handler to make permissions available in templates
@app.before_request
def add_permission_context():
    """Add permission context to Flask's g object for use in templates"""
    from flask import g
    
    user = get_current_user()
    if user:
        user_id = user.get('id') or user.get('user_id')
        if user_id:
            g.user_permissions = get_user_all_permissions(user_id)
            g.user_groups = get_user_groups(user_id)
        else:
            g.user_permissions = []
            g.user_groups = []
    else:
        g.user_permissions = []
        g.user_groups = []

# Add this route to your existing routes
@app.route('/groups/')
@permission_required(Permission.VIEW_USERS)
def group_management_page():
    """Group management page"""
    return render_template('group_management.html')

# Example of protecting an existing route with group permissions
@app.route('/admin/dashboard')
@permission_required(Permission.VIEW_ALL_DATA)
def admin_dashboard():
    """Admin dashboard - now protected with group permissions"""
    user = get_current_user()
    user_id = user.get('id') or user.get('user_id')
    
    # Get user's permissions for display
    user_permissions = get_user_all_permissions(user_id)
    
    return render_template('admin_dashboard.html', 
                         user=user, 
                         permissions=user_permissions)

# Example of a route that checks group membership
@app.route('/team/analytics')
def team_analytics():
    """Team analytics - requires team group membership"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = user.get('id') or user.get('user_id')
    user_groups = get_user_groups(user_id)
    
    # Find team groups
    team_groups = [group for group in user_groups if 'team' in group['name'].lower()]
    
    if not team_groups:
        return jsonify({'error': 'You must be a member of a team group to access this page'}), 403
    
    return render_template('team_analytics.html', 
                         user=user, 
                         team_groups=team_groups)

# Initialize the group system (run once)
def initialize_group_system_once():
    """Initialize the group system - call this once after app creation"""
    with app.app_context():
        try:
            initialize_group_system()
            print("Group system initialized successfully")
        except Exception as e:
            print(f"Error initializing group system: {e}")

# Add this to your main block
if __name__ == '__main__':
    # Your existing initialization code...
    
    # Initialize group system (run once)
    initialize_group_system_once()
    
    # Your existing app.run()...
    app.run(debug=True, host='0.0.0.0', port=5000)
