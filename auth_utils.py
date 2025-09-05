import hashlib

# Centralized path for local users CSV
USERS_FILE = 'logs/users.csv'

def hash_password(password: str) -> str:
    """Return SHA-256 hash of provided password (legacy/simple helper)."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


