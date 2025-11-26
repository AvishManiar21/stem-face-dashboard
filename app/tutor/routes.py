"""Tutor blueprint - placeholder"""
from flask import Blueprint

tutor_bp = Blueprint('tutor', __name__)

@tutor_bp.route('/dashboard')
def dashboard():
    return "Tutor Dashboard - TODO"
