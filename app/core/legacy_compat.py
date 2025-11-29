"""
Legacy compatibility layer for TutorAnalytics
Provides stub methods for backward compatibility
"""
import pandas as pd
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TutorAnalytics:
    """
    Legacy compatibility class for TutorAnalytics
    Provides minimal stub methods to prevent import errors
    """
    
    def __init__(self, face_log_file=None, max_date=None, custom_data=None):
        """Initialize with minimal setup"""
        self.data = pd.DataFrame()
        self.face_log_file = face_log_file
        
    def log_admin_action(self, action, target_user_email=None, details=""):
        """Log admin action to audit log"""
        try:
            audit_file = 'data/core/audit_log.csv'
            os.makedirs(os.path.dirname(audit_file), exist_ok=True)
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'target_user_email': target_user_email or '',
                'details': details,
                'user_email': 'system'  # Will be set by caller if available
            }
            
            # Append to audit log
            df = pd.DataFrame([log_entry])
            if os.path.exists(audit_file):
                existing_df = pd.read_csv(audit_file)
                df = pd.concat([existing_df, df], ignore_index=True)
            df.to_csv(audit_file, index=False)
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
    
    def get_audit_logs(self, page=1, per_page=25):
        """Get audit logs with pagination"""
        try:
            audit_file = 'data/core/audit_log.csv'
            if not os.path.exists(audit_file):
                return {'logs': [], 'total': 0}
            
            df = pd.read_csv(audit_file)
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
    
    def get_dashboard_summary(self):
        """Get dashboard summary - returns empty summary for now"""
        return {
            'total_checkins': 0,
            'total_tutors': 0,
            'today_checkins': 0,
            'this_week_checkins': 0,
            'this_month_checkins': 0
        }
    
    def get_logs_for_collapsible_view(self):
        """Get logs for collapsible view - returns empty for now"""
        return {}
    
    def generate_alerts(self):
        """Generate alerts - returns empty for now"""
        return []

