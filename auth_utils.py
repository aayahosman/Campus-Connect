from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    """
    Decorator to enforce login requirements for Flask routes.
    This decorator checks if a user is logged in before allowing access to 
    the decorated function. If the user is not logged in, they are redirected 
    to the login page with a warning message.
    Args:
        f (function): The function to be decorated.
    Returns:
        function: The wrapped function that enforces login requirements.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            flash("You must be logged in to do that.", "warning")
            return redirect(url_for('auth.index'))
        return f(*args, **kwargs)
    return wrapper
