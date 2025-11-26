"""Admin blueprint - placeholder"""
from flask import Blueprint, render_template

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
def dashboard():
    return "Admin Dashboard - TODO"

@admin_bp.route('/settings')
def settings():
    return "Admin Settings - TODO (Feature toggles will go here)"
