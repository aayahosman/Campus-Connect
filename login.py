from flask import Blueprint, render_template, request, redirect, flash, session, url_for
import bcrypt
import cs304dbi as dbi
from db import login_db

auth_bp = Blueprint('auth', __name__)

def get_conn():
    """Obtain a database connection using the project's db wrapper."""
    return dbi.connect()

@auth_bp.route('/')
def index():
    if 'user_id' in session:
        return render_template(
            'greet.html',
            page_title='Home',
            full_name=session.get('full_name'),
            email=session.get('email')
        )
    else:
        return render_template('login.html', page_title='Login')
    
@auth_bp.route('/about')
def about():
    return render_template('about.html', page_title='About Us')

@auth_bp.route('/signup/')
def show_signup():
    return render_template('signup.html', page_title='Campus Connect: Sign Up')

@auth_bp.route('/join/', methods=['POST'])
def join():
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    passwd1 = request.form.get('password1')
    passwd2 = request.form.get('password2')
    role = request.form.get('role')

    if not (full_name and email and passwd1 and passwd2):
        flash('Please fill in all required fields')
        return redirect(url_for('auth.index'))

    if passwd1 != passwd2:
        flash('Passwords do not match')
        return redirect(url_for('auth.index'))

    hashed = bcrypt.hashpw(
        passwd1.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    conn = get_conn()
    try:
        uid = login_db.insert_user(conn, full_name, email, hashed, role)
    except Exception as err:
        err_str = str(err)
        if "1062" in err_str or "Duplicate entry" in err_str:
            flash("This email is already registered. Please log in instead.", "error")
        else:
            flash(f"Something went wrong: {err}", "error")
        return redirect(url_for('auth.index'))

    session['full_name'] = full_name
    session['user_id'] = uid
    session['email'] = email
    session['logged_in'] = True
    session['visits'] = 1

    return redirect(url_for('auth.user', email=email))

@auth_bp.route('/login/', methods=['POST'])
def login():
    email = request.form.get('email')
    passwd = request.form.get('password')

    if not (email and passwd):
        flash('Please supply both email and password')
        return redirect(url_for('auth.index'))

    conn = get_conn()
    row = login_db.get_login_row_by_email(conn, email)

    if row is None:
        flash('Login incorrect. Try again or join.')
        return redirect(url_for('auth.index'))

    stored = row['password_hash']
    if bcrypt.checkpw(passwd.encode('utf-8'), stored.encode('utf-8')):
        flash('Successfully logged in as ' + email)
        session['email'] = email
        session['user_id'] = row['user_id']
        session['full_name'] = row['full_name']
        session['logged_in'] = True
        session['visits'] = 1
        return redirect(url_for('auth.user', email=email))
    else:
        flash('Login incorrect. Try again or join.')
        return redirect(url_for('auth.index'))

@auth_bp.route('/user/<email>')
def user(email):
    if 'email' in session and session.get('email') == email:
        user_id = session.get('user_id')
        session['visits'] = 1 + int(session.get('visits', 0))
        return render_template(
            'greet.html',
            page_title=f'Welcome {email}',
            email=email,
            full_name=session.get('full_name'),
            user_id=user_id,
            visits=session['visits']
        )
    else:
        flash('You are not logged in. Please login or join.')
        return redirect(url_for('auth.index'))

@auth_bp.route('/logout/')
def logout():
    if 'email' in session:
        session.pop('email', None)
        session.pop('user_id', None)
        session.pop('full_name', None)
        session.pop('logged_in', None)
        flash('You are logged out')
    else:
        flash('You are not logged in. Please login or join')

    return redirect(url_for('auth.index'))
