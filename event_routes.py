from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from cs304dbi import connect
import cs304dbi as dbi
import datetime
dbi.conf('cs304jas_db')

event_bp = Blueprint('event_bp', __name__, url_prefix='/events')

def getConn():
    return connect()

# Read events
@event_bp.route('/')
def list_events():
    conn = getConn()
    curs = conn.cursor()
    curs.execute('''
        select * from events ORDER BY created_at DESC
        ''')
    events = curs.fetchall()
    return render_template('events/list.html', events=events)

# Add events
@event_bp.route('/add', methods = ['GET', 'POST'])
def add_event():
    conn = getConn()
    curs = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        date_of_event = request.form['date_of_event']
        category = request.form['category']
        description = request.form['description']
        contact_info = request.form['contact_info']
        status = request.form['status']

        # temp placeholder
        created_by = session.get('user_id', 1)
        created_at = datetime.datetime.now()

        curs.execute('''
            insert into events(title, date_of_event, category, description,
                            contact_info, status, created_by, created_at)
            values(%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (title, date_of_event, category, description, contact_info, status,
                created_by, created_at))
        conn.commit()
        flash("Event created successfully!")
        return redirect(url_for('event_bp.list_events'))

    return render_template('add_event.html')

# Shows event full details & RSVP
@event_bp.route('/<int:event_id>')
def event_details(event_id):
    conn = getConn()
    curs = conn.cursor()
