from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            flash("You must be logged in to do that.", "warning")
            return redirect(url_for('auth.index'))
        return f(*args, **kwargs)
    return wrapper
