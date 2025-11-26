"""Auth blueprint - placeholder"""
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    return "Login page - TODO"

@auth_bp.route('/logout')
def logout():
    return "Logout - TODO"
