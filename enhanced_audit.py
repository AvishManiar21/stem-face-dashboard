"""
Enhanced Audit Logging System for Permission and Security Events
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import pandas as pd
from flask import request, session, g

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Types of audit events"""
    # Authentication Events
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    
    # Permission Events
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    ROLE_CHANGE = "ROLE_CHANGE"
    PERMISSION_ESCALATION_ATTEMPT = "PERMISSION_ESCALATION_ATTEMPT"
    
    # User Management Events
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    USER_ACTIVATED = "USER_ACTIVATED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    
    # Data Access Events
    DATA_ACCESSED = "DATA_ACCESSED"
    DATA_EXPORTED = "DATA_EXPORTED"
    DATA_MODIFIED = "DATA_MODIFIED"
    SENSITIVE_DATA_ACCESSED = "SENSITIVE_DATA_ACCESSED"
    
    # System Events
    SYSTEM_SETTINGS_CHANGED = "SYSTEM_SETTINGS_CHANGED"
    CONFIGURATION_CHANGED = "CONFIGURATION_CHANGED"
    SECURITY_EVENT = "SECURITY_EVENT"
    
    # API Events
    API_ACCESS = "API_ACCESS"
    API_ERROR = "API_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

class AuditSeverity(Enum):
    """Audit event severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class EnhancedAuditLogger:
    """Enhanced audit logging system"""
    
    def __init__(self, log_file: str = "logs/audit_log.csv"):
        self.log_file = log_file
        self.ensure_log_directory()
        self.initialize_log_file()
    
    def ensure_log_directory(self):
        """Ensure log directory exists"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def initialize_log_file(self):
        """Initialize audit log file with headers if it doesn't exist"""
        if not os.path.exists(self.log_file):
            headers = [
                'timestamp', 'event_type', 'severity', 'user_id', 'user_email', 
                'user_role', 'ip_address', 'user_agent', 'endpoint', 'method',
                'target_user', 'target_resource', 'details', 'success', 'error_message'
            ]
            df = pd.DataFrame(columns=headers)
            df.to_csv(self.log_file, index=False)
    
    def log_event(self, 
                  event_type: AuditEventType,
                  severity: AuditSeverity = AuditSeverity.MEDIUM,
                  user_id: str = None,
                  user_email: str = None,
                  user_role: str = None,
                  target_user: str = None,
                  target_resource: str = None,
                  details: str = None,
                  success: bool = True,
                  error_message: str = None,
                  additional_data: Dict[str, Any] = None):
        """Log an audit event"""
        
        # Get request context if available
        ip_address = self._get_client_ip()
        user_agent = self._get_user_agent()
        endpoint = self._get_endpoint()
        method = self._get_method()
        
        # Get user context if not provided
        if not user_id or not user_email or not user_role:
            user_context = self._get_user_context()
            user_id = user_id or user_context.get('user_id')
            user_email = user_email or user_context.get('user_email')
            user_role = user_role or user_context.get('user_role')
        
        # Create audit record
        audit_record = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type.value,
            'severity': severity.value,
            'user_id': user_id or 'anonymous',
            'user_email': user_email or 'anonymous',
            'user_role': user_role or 'unknown',
            'ip_address': ip_address,
            'user_agent': user_agent,
            'endpoint': endpoint,
            'method': method,
            'target_user': target_user,
            'target_resource': target_resource,
            'details': details or '',
            'success': success,
            'error_message': error_message or '',
            'additional_data': json.dumps(additional_data) if additional_data else ''
        }
        
        # Write to CSV
        try:
            df = pd.DataFrame([audit_record])
            df.to_csv(self.log_file, mode='a', header=False, index=False)
            
            # Also log to standard logger for immediate visibility
            log_message = f"{event_type.value}: {user_email} - {details or 'No details'}"
            if severity == AuditSeverity.CRITICAL:
                logger.critical(log_message)
            elif severity == AuditSeverity.HIGH:
                logger.error(log_message)
            elif severity == AuditSeverity.MEDIUM:
                logger.warning(log_message)
            else:
                logger.info(log_message)
                
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def _get_client_ip(self) -> str:
        """Get client IP address"""
        if request:
            return request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        return 'unknown'
    
    def _get_user_agent(self) -> str:
        """Get user agent string"""
        if request:
            return request.headers.get('User-Agent', 'unknown')
        return 'unknown'
    
    def _get_endpoint(self) -> str:
        """Get current endpoint"""
        if request:
            return request.endpoint or 'unknown'
        return 'unknown'
    
    def _get_method(self) -> str:
        """Get HTTP method"""
        if request:
            return request.method
        return 'unknown'
    
    def _get_user_context(self) -> Dict[str, str]:
        """Get current user context"""
        try:
            # Try to get from Flask g context
            if hasattr(g, 'permission_context') and g.permission_context:
                context = g.permission_context
                return {
                    'user_id': context.user.get('id') if context.user else None,
                    'user_email': context.user.get('email') if context.user else None,
                    'user_role': context.role
                }
            
            # Try to get from session
            if session and 'user' in session:
                user = session['user']
                return {
                    'user_id': user.get('id'),
                    'user_email': user.get('email'),
                    'user_role': user.get('user_metadata', {}).get('role', 'unknown')
                }
        except Exception as e:
            logger.warning(f"Failed to get user context: {e}")
        
        return {}
    
    def log_permission_event(self, 
                           event_type: AuditEventType,
                           permission: str,
                           target_user: str = None,
                           success: bool = True,
                           details: str = None):
        """Log permission-related events"""
        self.log_event(
            event_type=event_type,
            severity=AuditSeverity.HIGH if not success else AuditSeverity.MEDIUM,
            target_user=target_user,
            target_resource=permission,
            details=details or f"Permission: {permission}",
            success=success
        )
    
    def log_data_access(self, 
                       data_type: str,
                       access_scope: str,
                       record_count: int = None,
                       success: bool = True):
        """Log data access events"""
        details = f"Data type: {data_type}, Scope: {access_scope}"
        if record_count is not None:
            details += f", Records: {record_count}"
        
        self.log_event(
            event_type=AuditEventType.DATA_ACCESSED,
            severity=AuditSeverity.MEDIUM,
            target_resource=data_type,
            details=details,
            success=success
        )
    
    def log_security_event(self, 
                          event_description: str,
                          severity: AuditSeverity = AuditSeverity.HIGH,
                          additional_data: Dict[str, Any] = None):
        """Log security-related events"""
        self.log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            severity=severity,
            details=event_description,
            additional_data=additional_data
        )
    
    def get_audit_logs(self, 
                      start_date: str = None,
                      end_date: str = None,
                      event_type: AuditEventType = None,
                      user_email: str = None,
                      severity: AuditSeverity = None,
                      limit: int = 1000) -> pd.DataFrame:
        """Retrieve audit logs with filtering"""
        try:
            df = pd.read_csv(self.log_file)
            
            # Apply filters
            if start_date:
                df = df[df['timestamp'] >= start_date]
            if end_date:
                df = df[df['timestamp'] <= end_date]
            if event_type:
                df = df[df['event_type'] == event_type.value]
            if user_email:
                df = df[df['user_email'] == user_email]
            if severity:
                df = df[df['severity'] == severity.value]
            
            # Sort by timestamp (newest first) and limit
            df = df.sort_values('timestamp', ascending=False).head(limit)
            
            return df
        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {e}")
            return pd.DataFrame()
    
    def get_security_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get security summary for the last N days"""
        try:
            end_date = datetime.now().isoformat()
            start_date = (datetime.now() - pd.Timedelta(days=days)).isoformat()
            
            df = self.get_audit_logs(start_date=start_date, end_date=end_date)
            
            if df.empty:
                return {"message": "No audit data available"}
            
            summary = {
                "period_days": days,
                "total_events": len(df),
                "events_by_type": df['event_type'].value_counts().to_dict(),
                "events_by_severity": df['severity'].value_counts().to_dict(),
                "failed_events": len(df[df['success'] == False]),
                "unique_users": df['user_email'].nunique(),
                "most_active_user": df['user_email'].value_counts().head(1).to_dict(),
                "recent_critical_events": df[df['severity'] == 'CRITICAL'].head(10).to_dict('records')
            }
            
            return summary
        except Exception as e:
            logger.error(f"Failed to generate security summary: {e}")
            return {"error": str(e)}

# Global audit logger instance
audit_logger = EnhancedAuditLogger()

# Convenience functions for common audit events
def log_login_success(user_email: str, user_role: str):
    """Log successful login"""
    audit_logger.log_event(
        event_type=AuditEventType.LOGIN_SUCCESS,
        severity=AuditSeverity.LOW,
        user_email=user_email,
        user_role=user_role,
        details="User logged in successfully"
    )

def log_login_failure(user_email: str, reason: str = None):
    """Log failed login attempt"""
    audit_logger.log_event(
        event_type=AuditEventType.LOGIN_FAILURE,
        severity=AuditSeverity.MEDIUM,
        user_email=user_email,
        details=f"Login failed: {reason or 'Invalid credentials'}"
    )

def log_permission_denied(permission: str, user_email: str, target: str = None):
    """Log permission denied event"""
    audit_logger.log_permission_event(
        event_type=AuditEventType.PERMISSION_DENIED,
        permission=permission,
        target_user=user_email,
        success=False,
        details=f"Access denied to {permission}" + (f" for {target}" if target else "")
    )

def log_role_change(target_user: str, old_role: str, new_role: str, changed_by: str):
    """Log role change event"""
    audit_logger.log_event(
        event_type=AuditEventType.ROLE_CHANGE,
        severity=AuditSeverity.HIGH,
        target_user=target_user,
        details=f"Role changed from {old_role} to {new_role} by {changed_by}"
    )

def log_data_export(data_type: str, record_count: int, user_email: str):
    """Log data export event"""
    audit_logger.log_event(
        event_type=AuditEventType.DATA_EXPORTED,
        severity=AuditSeverity.MEDIUM,
        user_email=user_email,
        target_resource=data_type,
        details=f"Exported {record_count} {data_type} records"
    )

def log_security_violation(violation_type: str, details: str, user_email: str = None):
    """Log security violation"""
    audit_logger.log_security_event(
        event_description=f"{violation_type}: {details}",
        severity=AuditSeverity.CRITICAL,
        additional_data={"violation_type": violation_type, "user_email": user_email}
    )
