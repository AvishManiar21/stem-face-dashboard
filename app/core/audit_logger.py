"""
Simple audit logging module
Replaces legacy TutorAnalytics audit logging
"""
import pandas as pd
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

AUDIT_LOG_FILE = 'data/core/audit_log.csv'

def log_admin_action(action, target_user_email=None, details="", user_email=None):
    """Log admin action to audit log CSV"""
    try:
        os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'target_user_email': target_user_email or '',
            'details': details,
            'user_email': user_email or 'system'
        }
        
        # Append to audit log
        df = pd.DataFrame([log_entry])
        if os.path.exists(AUDIT_LOG_FILE):
            existing_df = pd.read_csv(AUDIT_LOG_FILE)
            df = pd.concat([existing_df, df], ignore_index=True)
        df.to_csv(AUDIT_LOG_FILE, index=False)
        
        logger.info(f"Audit log: {action} by {user_email or 'system'}")
    except Exception as e:
        logger.error(f"Failed to log admin action: {e}")

def get_audit_logs(page=1, per_page=25):
    """Get audit logs with pagination"""
    try:
        if not os.path.exists(AUDIT_LOG_FILE):
            return {'logs': [], 'total': 0}
        
        df = pd.read_csv(AUDIT_LOG_FILE)
        total = len(df)
        
        # Paginate
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_df = df.iloc[start_idx:end_idx]
        
        logs = paginated_df.to_dict('records')
        return {'logs': logs, 'total': total}
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        return {'logs': [], 'total': 0}

