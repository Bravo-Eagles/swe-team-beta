import bcrypt
from api import auth_api

def hash_password(password: str) -> str:
    """Return a bcrypt hash of the password, ready to store."""
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode()


def verify_password(password: str, stored_hash: str) -> bool:
    """Return True if the password matches the stored hash."""
    return bcrypt.checkpw(password.encode(), stored_hash.encode())

def signup_user_account():
    """Creates a User Account"""
    