# Enhanced Permission System Documentation

## Overview

The enhanced permission system provides granular access control for the Tutor Face Recognition Dashboard. It replaces the basic role-based system with a comprehensive capability-based permission model.

## Key Features

- **Granular Permissions**: 20+ specific permissions instead of just 4 roles
- **Role Hierarchy**: 5 levels from Tutor to Super Admin
- **Data Access Control**: Automatic filtering based on user permissions
- **Audit Logging**: Comprehensive tracking of all permission-related events
- **Permission Middleware**: Automatic permission checking for routes
- **UI Management**: Web interface for permission management

## Architecture

### Core Components

1. **`permissions.py`** - Core permission system with roles and capabilities
2. **`permission_middleware.py`** - Flask middleware for automatic permission checking
3. **`enhanced_audit.py`** - Comprehensive audit logging system
4. **`test_permissions.py`** - Complete test suite for permission functionality

### Permission Model

#### Roles (Hierarchical)

1. **Tutor** (Level 1)
   - Basic data access (own data only)
   - View face recognition logs

2. **Lead Tutor** (Level 2)
   - Team data access
   - User management (read-only)
   - Shift management
   - Basic analytics

3. **Manager** (Level 3)
   - All data access
   - User management (create, edit, change roles)
   - Advanced analytics
   - Report generation
   - Audit log access

4. **Admin** (Level 4)
   - All manager permissions
   - User deletion
   - System settings management
   - Face recognition management

5. **Super Admin** (Level 5)
   - All permissions
   - Complete system control

#### Permissions (Capabilities)

**User Management**
- `view_users` - View user list
- `create_users` - Create new users
- `edit_users` - Edit user information
- `delete_users` - Delete users
- `change_user_roles` - Change user roles
- `activate_deactivate_users` - Activate/deactivate users

**Data Access**
- `view_all_data` - Access to all data
- `view_own_data` - Access to own data only
- `view_team_data` - Access to team data
- `export_data` - Export data functionality

**Analytics & Reports**
- `view_analytics` - Basic analytics access
- `view_advanced_analytics` - Advanced analytics
- `generate_reports` - Generate reports

**System Administration**
- `manage_system_settings` - System configuration
- `view_audit_logs` - Audit log access
- `manage_shifts` - Shift management

**Face Recognition**
- `manage_face_recognition` - Face recognition settings
- `view_face_logs` - Face recognition logs
- `manage_face_database` - Face database management

## Usage

### Route Protection

#### Basic Permission Check
```python
from permissions import permission_required, Permission

@app.route('/api/admin/users')
@permission_required(Permission.VIEW_USERS)
def get_users():
    return jsonify(users)
```

#### Multiple Permissions
```python
from permissions import permissions_required

@app.route('/api/admin/create-user')
@permissions_required([Permission.CREATE_USERS, Permission.VIEW_USERS])
def create_user():
    return jsonify({"message": "User created"})
```

#### Data Access Control
```python
from permission_middleware import require_data_access

@app.route('/api/data')
@require_data_access("team")  # Requires team-level access
def get_data():
    return jsonify(data)
```

#### Permission Context
```python
from permission_middleware import permission_context

@app.route('/api/dashboard')
@permission_context
def dashboard():
    context = g.permission_context
    # Access user permissions, role, etc.
    return render_template('dashboard.html', context=context)
```

### Data Filtering

The system automatically filters data based on user permissions:

```python
from permissions import filter_data_by_permissions

# Filter data automatically
filtered_data = filter_data_by_permissions(
    df, 
    user_role='tutor', 
    user_tutor_id='123', 
    user_email='user@example.com'
)
```

### Audit Logging

#### Log Permission Events
```python
from enhanced_audit import log_permission_denied, log_role_change

# Log permission denied
log_permission_denied('create_users', 'user@example.com', 'admin_panel')

# Log role change
log_role_change('target@example.com', 'tutor', 'manager', 'admin@example.com')
```

#### Custom Audit Events
```python
from enhanced_audit import audit_logger, AuditEventType, AuditSeverity

audit_logger.log_event(
    event_type=AuditEventType.DATA_EXPORTED,
    severity=AuditSeverity.MEDIUM,
    user_email='user@example.com',
    details='Exported 1000 records'
)
```

## API Endpoints

### User Capabilities
- `GET /api/user/capabilities` - Get current user's capabilities

### Permission Management
- `GET /permission-management` - Permission management UI
- `GET /api/admin/audit-logs` - Get audit logs

### Admin Functions
- `GET /api/admin/users` - Get users (permission-filtered)
- `POST /api/admin/change-role` - Change user role
- `POST /api/admin/delete-user` - Delete user

## Security Features

### Permission Escalation Prevention
- Users cannot grant permissions they don't have
- Role changes are restricted based on hierarchy
- Self-modification is limited

### Data Isolation
- Automatic data filtering based on permissions
- Sensitive data access logging
- Audit trail for all permission changes

### Rate Limiting
- API rate limiting for sensitive operations
- Brute force protection for authentication
- Suspicious activity detection

## Testing

Run the comprehensive test suite:

```bash
python test_permissions.py
```

The test suite covers:
- Permission system functionality
- Middleware integration
- Data filtering
- Security aspects
- API endpoints

## Migration from Old System

The new system is backward compatible. Existing routes will continue to work, but you can gradually migrate to the new permission system:

1. **Phase 1**: Add permission middleware to new routes
2. **Phase 2**: Update existing routes to use new decorators
3. **Phase 3**: Implement data filtering
4. **Phase 4**: Add audit logging

## Configuration

### Environment Variables
```bash
# Audit logging
AUDIT_LOG_FILE=logs/audit_log.csv

# Permission settings
DEFAULT_USER_ROLE=tutor
ENABLE_PERMISSION_AUDIT=true
```

### Permission Customization

To add new permissions:

1. Add to `Permission` enum in `permissions.py`
2. Update `ROLE_PERMISSIONS` mapping
3. Add to UI in `permission_management.html`
4. Update tests in `test_permissions.py`

## Monitoring and Maintenance

### Audit Log Analysis
```python
from enhanced_audit import audit_logger

# Get security summary
summary = audit_logger.get_security_summary(days=7)
print(f"Total events: {summary['total_events']}")
print(f"Failed events: {summary['failed_events']}")
```

### Permission Health Check
```python
from permissions import PermissionManager

# Check if user has required permissions
has_permission = PermissionManager.has_permission('admin', Permission.CREATE_USERS)
```

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   - Check user role and permissions
   - Verify permission decorators are applied
   - Check audit logs for details

2. **Data Not Filtering**
   - Ensure `filter_data_by_permissions` is called
   - Check user context is loaded
   - Verify data has required columns

3. **Audit Logging Issues**
   - Check log file permissions
   - Verify audit logger is initialized
   - Check for disk space issues

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger('permissions').setLevel(logging.DEBUG)
logging.getLogger('permission_middleware').setLevel(logging.DEBUG)
```

## Best Practices

1. **Principle of Least Privilege**: Grant minimum required permissions
2. **Regular Audits**: Review permissions and access logs regularly
3. **Role Separation**: Use different roles for different responsibilities
4. **Data Classification**: Mark sensitive data and restrict access
5. **Monitoring**: Set up alerts for suspicious activities

## Future Enhancements

- **Dynamic Permissions**: Runtime permission changes
- **Permission Groups**: Group permissions for easier management
- **Time-based Access**: Temporary permissions with expiration
- **Geographic Restrictions**: Location-based access control
- **Integration**: LDAP/Active Directory integration
