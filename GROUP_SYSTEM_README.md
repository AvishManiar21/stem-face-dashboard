# User Grouping and Permission Control System

This system adds user grouping and granular permission control to your existing Flask dashboard. It's designed to work with your current authentication system and provides both role-based and group-based permissions.

## Features

- **SQLAlchemy Models**: Group, GroupMember, Permission, and GroupPermission models
- **Flask Routes**: Complete CRUD operations for group management
- **Permission Helpers**: Functions to check user permissions across groups
- **HTML Templates**: Ready-to-use templates for group management
- **Integration Examples**: Examples of how to protect routes and display conditional UI

## Files Added

1. `models.py` - SQLAlchemy models for the group system
2. `group_routes.py` - Flask routes for group management
3. `group_helpers.py` - Helper functions for permission checking
4. `protected_routes_example.py` - Examples of protected routes
5. `templates/group_management.html` - Group management interface
6. `templates/permission_example.html` - Example template with conditional UI
7. `init_group_system.py` - Database initialization script

## Installation

### 1. Install Dependencies

Add Flask-SQLAlchemy to your requirements.txt:

```bash
echo "Flask-SQLAlchemy==3.0.5" >> requirements.txt
pip install Flask-SQLAlchemy==3.0.5
```

### 2. Update Your Main App

Add the following to your `app.py`:

```python
# Add these imports
from flask_sqlalchemy import SQLAlchemy
from models import db, Group, GroupMember, Permission, GroupPermission, User
from group_routes import group_bp
from group_helpers import initialize_group_system

# Initialize SQLAlchemy
db.init_app(app)

# Register the group blueprint
app.register_blueprint(group_bp)

# Initialize the group system (run once)
with app.app_context():
    initialize_group_system()
```

### 3. Configure Database

Set your database URL in your environment or app config:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
# or for PostgreSQL: 'postgresql://user:password@localhost/dbname'
# or for MySQL: 'mysql://user:password@localhost/dbname'
```

### 4. Initialize Database

Run the initialization script:

```bash
python init_group_system.py
```

## Usage

### 1. Basic Permission Checking

```python
from group_helpers import user_has_group_permission, get_user_all_permissions

# Check if user has a specific permission in a group
user_id = 1
group_id = 1
permission_name = 'view_users'
has_permission = user_has_group_permission(user_id, group_id, permission_name)

# Get all permissions for a user (role-based + group-based)
user_permissions = get_user_all_permissions(user_id)
```

### 2. Protecting Routes

```python
from group_helpers import group_permission_required

@app.route('/admin/dashboard')
@group_permission_required('view_all_data')
def admin_dashboard():
    return render_template('admin_dashboard.html')
```

### 3. Conditional UI in Templates

```html
<!-- Show button only if user has permission -->
{% if 'create_users' in g.user_permissions %}
<button class="btn btn-primary">Create User</button>
{% endif %}

<!-- Show section only if user is in a specific group -->
{% if g.user_groups %}
{% for group in g.user_groups %}
    {% if group.name == 'Administrators' %}
    <div class="admin-section">Admin content here</div>
    {% endif %}
{% endfor %}
{% endif %}
```

### 4. Group Management

Access the group management interface at `/groups/` (requires appropriate permissions).

## API Endpoints

### Groups
- `GET /groups/` - List all groups
- `POST /groups/create` - Create a new group
- `GET /groups/<id>` - Get group details
- `GET /groups/<id>/members` - Get group members
- `POST /groups/<id>/add-member` - Add member to group
- `POST /groups/<id>/remove-member` - Remove member from group
- `GET /groups/<id>/permissions` - Get group permissions
- `POST /groups/<id>/assign-permission` - Assign permission to group
- `POST /groups/<id>/remove-permission` - Remove permission from group

### Utilities
- `GET /groups/permissions` - List all permissions
- `GET /groups/users` - List all users

## Permission System

### Default Permissions

The system includes these default permissions:

**User Management:**
- `view_users` - View user information
- `create_users` - Create new users
- `edit_users` - Edit user information
- `delete_users` - Delete users
- `change_user_roles` - Change user roles
- `activate_deactivate_users` - Activate/deactivate users

**Data Access:**
- `view_all_data` - View all system data
- `view_own_data` - View own data only
- `view_team_data` - View team data
- `export_data` - Export data

**Analytics:**
- `view_analytics` - View basic analytics
- `view_advanced_analytics` - View advanced analytics
- `generate_reports` - Generate reports

**System:**
- `manage_system_settings` - Manage system settings
- `view_audit_logs` - View audit logs
- `manage_shifts` - Manage shifts and schedules

**Face Recognition:**
- `manage_face_recognition` - Manage face recognition system
- `view_face_logs` - View face recognition logs
- `manage_face_database` - Manage face database

### Permission Hierarchy

1. **Role-based permissions** - Inherited from user role
2. **Group-based permissions** - Additional permissions from group membership
3. **Combined permissions** - Union of both role and group permissions

## Integration with Existing System

### 1. Update Your User Model

If you have an existing User model, add these relationships:

```python
# Add to your existing User model
led_groups = relationship("Group", foreign_keys="Group.lead_user_id", back_populates="lead_user")
group_memberships = relationship("GroupMember", back_populates="user")

def get_groups(self):
    """Get all groups this user belongs to"""
    return [membership.group for membership in self.group_memberships if membership.active]

def get_led_groups(self):
    """Get all groups this user leads"""
    return [group for group in self.led_groups if group.active]
```

### 2. Add Permission Context to Templates

Add this to your main app to make permissions available in templates:

```python
@app.before_request
def add_permission_context():
    from flask import g
    from group_helpers import get_user_all_permissions, get_user_groups
    
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
```

### 3. Update Navigation

Update your navigation to show/hide items based on permissions:

```html
<!-- Example navigation with permission checks -->
<nav>
    {% if 'view_users' in g.user_permissions %}
    <a href="/admin/users">User Management</a>
    {% endif %}
    
    {% if 'view_analytics' in g.user_permissions %}
    <a href="/analytics">Analytics</a>
    {% endif %}
    
    {% if g.user_groups %}
    <a href="/groups/">Group Management</a>
    {% endif %}
</nav>
```

## Security Considerations

1. **Always validate permissions server-side** - Don't rely only on client-side checks
2. **Use the provided decorators** - They handle authentication and authorization
3. **Audit permission changes** - Log when permissions are granted or revoked
4. **Regular permission reviews** - Periodically review user permissions
5. **Principle of least privilege** - Only grant necessary permissions

## Troubleshooting

### Common Issues

1. **Database not initialized**: Run `python init_group_system.py`
2. **Permission denied errors**: Check if user has required permissions
3. **Template errors**: Ensure `g.user_permissions` and `g.user_groups` are available
4. **Import errors**: Make sure all files are in the correct directory

### Debugging

Enable debug logging to see permission checks:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Customization

### Adding New Permissions

1. Add to the `create_default_permissions()` function in `init_group_system.py`
2. Run the initialization script again
3. Assign permissions to groups as needed

### Custom Permission Categories

Modify the permission categories in the initialization script to match your needs.

### Custom Group Types

Create different group types with specific permission sets by modifying the `assign_permissions_to_groups()` function.

## Support

For issues or questions:
1. Check the error logs
2. Verify database initialization
3. Ensure all dependencies are installed
4. Check that the user has the required permissions

## License

This system is provided as-is for integration with your existing Flask dashboard.
