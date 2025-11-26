# Feature Toggle System - Quick Reference

## Overview

The feature toggle system allows runtime control of features without code changes or redeployment.

---

## Configuration Layers

### Layer 1: Environment Variables (`.env`)
```bash
ENABLE_FACE_RECOGNITION=false
ENABLE_LEGACY_ANALYTICS=false
MAINTENANCE_MODE=false
```
- Used for deployment-time configuration
- Loaded on application startup
- Requires restart to change

### Layer 2: Runtime Config (`data/system_config.csv`)
```csv
setting_key,setting_value,description,last_updated
face_recognition_enabled,false,Enable face recognition module,2025-11-26T12:27:00
legacy_analytics_enabled,false,Enable legacy analytics charts,2025-11-26T12:27:00
maintenance_mode,false,Enable maintenance mode access,2025-11-26T12:27:00
```
- Can be changed at runtime
- Persists across restarts
- Admin UI can modify (future)

---

## Python API

### Check if Feature is Enabled

```python
from app.utils.feature_flags import is_feature_enabled

if is_feature_enabled('face_recognition'):
    # Feature is enabled
    show_face_recognition_ui()
else:
    # Feature is disabled
    show_standard_ui()
```

### Toggle a Feature

```python
from app.utils.feature_flags import toggle_feature

# Enable a feature
toggle_feature('face_recognition', True)

# Disable a feature
toggle_feature('face_recognition', False)
```

### Get All Features

```python
from app.utils.feature_flags import get_all_features

features = get_all_features()
# Returns:
# {
#     'face_recognition': {
#         'enabled': False,
#         'description': 'Enable face recognition module',
#         'last_updated': '2025-11-26T12:27:00'
#     },
#     ...
# }
```

---

## Route Protection

### Using the Decorator

```python
from flask import Blueprint, render_template
from app.utils.feature_flags import feature_required

legacy_bp = Blueprint('legacy', __name__)

@legacy_bp.route('/dashboard')
@feature_required('face_recognition')
def legacy_dashboard():
    """This route only accessible when face_recognition is enabled"""
    return render_template('legacy/dashboard.html')
```

**Behavior:**
- If feature is **enabled**: Route works normally
- If feature is **disabled**: Redirects to home with warning message

---

## Template Usage

### Check Feature in Templates

```html
{% if is_feature_enabled('face_recognition') %}
    <a href="{{ url_for('legacy.dashboard') }}">Face Recognition</a>
{% endif %}
```

### Access Config Values

```html
{% if config.ENABLE_FACE_RECOGNITION %}
    <!-- Feature enabled via environment -->
{% endif %}
```

---

## Blueprint Registration

### Conditional Loading

```python
# In app/__init__.py
def register_blueprints(app):
    # Always load core blueprints
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Conditionally load legacy blueprint
    if app.config['ENABLE_FACE_RECOGNITION'] or is_feature_enabled('face_recognition'):
        from app.legacy.routes import legacy_bp
        app.register_blueprint(legacy_bp, url_prefix='/legacy')
```

**Benefits:**
- Legacy code not loaded when disabled
- Reduces memory footprint
- Faster startup time

---

## Available Features

| Feature Name | Config Key | Description |
|--------------|------------|-------------|
| `face_recognition` | `ENABLE_FACE_RECOGNITION` | Face recognition attendance system |
| `legacy_analytics` | `ENABLE_LEGACY_ANALYTICS` | Old analytics charts and forecasting |
| `maintenance_mode` | `MAINTENANCE_MODE` | Admin-only maintenance access |

---

## Adding New Features

### 1. Add to Config

**File:** `app/config.py`
```python
class Config:
    # Add new feature flag
    ENABLE_NEW_FEATURE = os.getenv('ENABLE_NEW_FEATURE', 'false').lower() == 'true'
```

### 2. Add to System Config

**File:** `data/system_config.csv`
```csv
new_feature_enabled,false,Description of new feature,2025-11-26T12:00:00
```

### 3. Use in Code

```python
from app.utils.feature_flags import is_feature_enabled, feature_required

# Check in code
if is_feature_enabled('new_feature'):
    do_something()

# Protect route
@feature_required('new_feature')
def new_feature_page():
    return render_template('new_feature.html')
```

---

## Admin UI (Future)

### Toggle Features via Web Interface

```
/admin/settings
├── Feature Toggles
│   ├── [x] Face Recognition
│   ├── [ ] Legacy Analytics
│   └── [ ] Maintenance Mode
└── [Save Changes]
```

**API Endpoint:**
```
POST /api/admin/settings/toggle
{
    "feature": "face_recognition",
    "enabled": true
}
```

---

## Best Practices

### 1. **Fail Safe**
- Features default to **disabled**
- Errors result in **disabled** state
- Prevents accidental exposure

### 2. **Clear Naming**
- Use descriptive feature names
- Match config keys to feature names
- Add helpful descriptions

### 3. **Logging**
- Log feature toggle changes
- Track who changed what
- Audit trail for compliance

### 4. **Testing**
- Test both enabled and disabled states
- Verify route protection
- Check UI conditional rendering

---

## Troubleshooting

### Feature Not Toggling

**Check:**
1. Is `data/system_config.csv` writable?
2. Is the feature name spelled correctly?
3. Are there any errors in console?

**Solution:**
```python
# Verify feature status
from app.utils.feature_flags import get_all_features
print(get_all_features())
```

### Blueprint Not Loading

**Check:**
1. Is the feature enabled in config?
2. Is the blueprint import path correct?
3. Are there syntax errors in blueprint?

**Solution:**
```python
# Check config
from app import create_app
app = create_app()
print(app.config['ENABLE_FACE_RECOGNITION'])
```

### Config File Missing

**Auto-Creation:**
The system automatically creates `data/system_config.csv` with defaults if missing.

**Manual Creation:**
```python
from app.utils.feature_flags import ensure_config_file
ensure_config_file()
```

---

## Security Considerations

### 1. **Admin-Only Toggles**
Only admins should toggle features:
```python
@admin_required
def toggle_feature_endpoint():
    # Only admins can access
    pass
```

### 2. **Audit Logging**
Log all feature changes:
```python
def toggle_feature(feature_name, enabled):
    # ... toggle logic ...
    log_audit_event(
        action='FEATURE_TOGGLE',
        details=f'{feature_name} set to {enabled}'
    )
```

### 3. **Validation**
Validate feature names:
```python
VALID_FEATURES = ['face_recognition', 'legacy_analytics', 'maintenance_mode']

def toggle_feature(feature_name, enabled):
    if feature_name not in VALID_FEATURES:
        raise ValueError(f'Invalid feature: {feature_name}')
    # ... toggle logic ...
```

---

## Examples

### Example 1: Conditional Navigation

```html
<!-- templates/base.html -->
<nav>
    <a href="{{ url_for('admin.dashboard') }}">Dashboard</a>
    <a href="{{ url_for('tutor.schedule') }}">Schedule</a>
    
    {% if is_feature_enabled('face_recognition') %}
        <a href="{{ url_for('legacy.attendance') }}">Attendance</a>
    {% endif %}
    
    {% if is_feature_enabled('legacy_analytics') %}
        <a href="{{ url_for('legacy.charts') }}">Analytics</a>
    {% endif %}
</nav>
```

### Example 2: Feature-Gated API

```python
# app/api/routes.py
from flask import Blueprint, jsonify
from app.utils.feature_flags import is_feature_enabled

api_bp = Blueprint('api', __name__)

@api_bp.route('/attendance/stats')
def attendance_stats():
    if not is_feature_enabled('face_recognition'):
        return jsonify({'error': 'Feature disabled'}), 403
    
    # Return attendance statistics
    return jsonify(get_attendance_stats())
```

### Example 3: Maintenance Mode

```python
# app/__init__.py
@app.before_request
def check_maintenance_mode():
    if is_feature_enabled('maintenance_mode'):
        if not current_user.is_admin:
            return render_template('maintenance.html'), 503
```

---

## Future Enhancements

### Planned Features:
- [ ] Admin UI for toggling features
- [ ] Feature scheduling (enable/disable at specific times)
- [ ] User-level feature flags (beta testing)
- [ ] Feature usage analytics
- [ ] A/B testing support

---

**Last Updated:** November 26, 2025  
**Version:** 1.0
