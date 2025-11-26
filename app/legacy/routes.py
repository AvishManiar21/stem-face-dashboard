"""Legacy blueprint - Face recognition features (toggleable)"""
from flask import Blueprint
from app.utils.feature_flags import feature_required

legacy_bp = Blueprint('legacy', __name__)

@legacy_bp.route('/attendance')
@feature_required('face_recognition')
def attendance():
    return "Face Recognition Attendance - TODO (Legacy Feature)"

@legacy_bp.route('/analytics')
@feature_required('legacy_analytics')
def analytics():
    return "Legacy Analytics - TODO (Legacy Feature)"
