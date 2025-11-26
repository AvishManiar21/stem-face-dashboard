"""Feature flag utilities for toggling features on/off"""
import pandas as pd
import os
from datetime import datetime

CONFIG_FILE = 'data/system_config.csv'

def ensure_config_file():
    """Ensure system config file exists"""
    if not os.path.exists(CONFIG_FILE):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        df = pd.DataFrame(columns=['setting_key', 'setting_value', 'description', 'last_updated'])
        # Initialize default settings
        defaults = [
            {'setting_key': 'face_recognition_enabled', 'setting_value': 'false', 
             'description': 'Enable face recognition module', 'last_updated': datetime.now().isoformat()},
            {'setting_key': 'legacy_analytics_enabled', 'setting_value': 'false', 
             'description': 'Enable legacy analytics charts', 'last_updated': datetime.now().isoformat()},
            {'setting_key': 'maintenance_mode', 'setting_value': 'false', 
             'description': 'Enable maintenance mode access', 'last_updated': datetime.now().isoformat()},
        ]
        df = pd.DataFrame(defaults)
        df.to_csv(CONFIG_FILE, index=False)

def is_feature_enabled(feature_name):
    """
    Check if a feature is enabled
    
    Args:
        feature_name: Name of feature (e.g., 'face_recognition', 'legacy_analytics')
    
    Returns:
        bool: True if enabled, False otherwise
    """
    ensure_config_file()
    
    try:
        df = pd.read_csv(CONFIG_FILE)
        
        # Check if required columns exist
        if 'setting_key' not in df.columns or 'setting_value' not in df.columns:
            print(f"Warning: system_config.csv missing required columns")
            return False
        
        key = f'{feature_name}_enabled'
        feature_row = df[df['setting_key'] == key]
        
        if not feature_row.empty:
            value = str(feature_row.iloc[0]['setting_value']).strip().lower()
            return value == 'true'
    except FileNotFoundError:
        print(f"Warning: {CONFIG_FILE} not found, creating with defaults")
        ensure_config_file()
    except Exception as e:
        print(f"Warning: Error checking feature '{feature_name}': {e}")
    
    return False

def toggle_feature(feature_name, enabled):
    """
    Toggle a feature on/off
    
    Args:
        feature_name: Name of feature
        enabled: True to enable, False to disable
    
    Returns:
        bool: True if successful
    """
    ensure_config_file()
    
    try:
        df = pd.read_csv(CONFIG_FILE)
        key = f'{feature_name}_enabled'
        
        if key in df['setting_key'].values:
            df.loc[df['setting_key'] == key, 'setting_value'] = str(enabled).lower()
            df.loc[df['setting_key'] == key, 'last_updated'] = datetime.now().isoformat()
        else:
            new_row = {
                'setting_key': key,
                'setting_value': str(enabled).lower(),
                'description': f'Enable {feature_name} feature',
                'last_updated': datetime.now().isoformat()
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        df.to_csv(CONFIG_FILE, index=False)
        return True
    except Exception as e:
        print(f"Error toggling feature {feature_name}: {e}")
        return False

def get_all_features():
    """Get all feature flags and their status"""
    ensure_config_file()
    
    try:
        df = pd.read_csv(CONFIG_FILE)
        features = {}
        for _, row in df.iterrows():
            if row['setting_key'].endswith('_enabled'):
                feature_name = row['setting_key'].replace('_enabled', '')
                features[feature_name] = {
                    'enabled': row['setting_value'].lower() == 'true',
                    'description': row['description'],
                    'last_updated': row['last_updated']
                }
        return features
    except Exception as e:
        print(f"Error getting features: {e}")
        return {}

def feature_required(feature_name):
    """
    Decorator to require a feature to be enabled
    
    Usage:
        @feature_required('face_recognition')
        def attendance_page():
            return render_template('attendance.html')
    """
    from functools import wraps
    from flask import abort, flash, redirect, url_for
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not is_feature_enabled(feature_name):
                flash(f'This feature is currently disabled.', 'warning')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
