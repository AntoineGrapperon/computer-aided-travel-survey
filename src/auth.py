from src.config import ADMIN_PASSWORD

def check_password(password):
    """Verifies the administrative password."""
    return password == ADMIN_PASSWORD
