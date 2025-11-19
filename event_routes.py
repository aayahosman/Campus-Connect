from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from cs304dbi import connect
import cs304dbi as dbi
import datetime
from auth_utils import login_required
dbi.conf('cs304jas_db')

event_bp = Blueprint('event_bp', __name__, url_prefix='/events')

def getConn():
    return connect()

# Read events
@event_bp.route('/')
def list_events():
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)
    curs.execute('''
        select * from events ORDER BY created_at DESC
        ''')
    events = curs.fetchall()
    return render_template('events/list.html', events=events)

# Add events
@event_bp.route('/add', methods = ['GET', 'POST'])
@login_required
def add_event():
    conn = getConn()
    curs = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        date_of_event = request.form['date_of_event']
        description = request.form['description']
        
        created_by = session.get('user_id')
        if created_by is None:
            flash("You must be logged in to create events.", "warning")
            return redirect(url_for('auth.index'))

        created_at = datetime.datetime.now()

        curs.execute('''
            insert into events(title, date_of_event, description,
                                         created_by, created_at)
            values(%s, %s, %s, %s, %s)
        ''', (title, date_of_event, description, created_by, created_at))
        conn.commit()
        flash("Event created successfully!")
        return redirect(url_for('event_bp.list_events'))

    return render_template('events/add.html')

# Shows event full details & RSVP
@event_bp.route('/<int:event_id>')
def event_details(event_id):
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    # get the event
    curs.execute('select * from events where event_id = %s', (event_id,))
    event = curs.fetchone()

    if event is None:
        flash("Event not found.")
        return redirect(url_for('event_bp.list_events'))

    # get all rsvps for the attendees at event
    curs.execute('''
        select rsvp.status,
                rsvp.created_at,
                users.full_name as name
        from rsvp
        inner join users on rsvp.created_by = users.user_id
        where rsvp.event_id = %s
                 and rsvp.status in ('yes', 'maybe')
            order by
                case rsvp.status
                    when 'yes' then 1
                    when 'maybe' then 2
                end,
                case rsvp.status
                when 'yes' then rsvp.created_at
                else null
                end asc
        ''', (event_id,))
    rsvps = curs.fetchall()

    # get the current user's RSVP if exists
    user_id = session.get('user_id', 1)
    curs.execute('''
        select status
        from rsvp
        where event_id = %s and created_by = %s
    ''', (event_id, user_id))
    user_rsvp = curs.fetchone()

    return render_template('events/detail.html',
                                event = event,
                                rsvps = rsvps,
                                user_rsvp = user_rsvp)

# Update event
@event_bp.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    # Fetch the event once
    curs.execute('SELECT * FROM events WHERE event_id=%s', (event_id,))
    event = curs.fetchone()

    if event is None:
        flash("Event not found.", "warning")
        return redirect(url_for('event_bp.list_events'))

    # Ownership check
    if event['created_by'] != session.get('user_id'):
        flash("You can only edit events you created!", "warning")
        return redirect(url_for('event_bp.list_events'))

    if request.method == 'POST':
        title = request.form['title']
        date_of_event = request.form['date_of_event']
        description = request.form['description']

        curs.execute('''
            UPDATE events
            SET title=%s, date_of_event=%s, description=%s
            WHERE event_id=%s
        ''', (title, date_of_event, description, event_id))

        conn.commit()
        flash("Event updated successfully!")
        return redirect(url_for('event_bp.list_events'))

    # Format datetime for editing form
    if event['date_of_event']:
        event['date_of_event'] = event['date_of_event'].strftime('%Y-%m-%dT%H:%M')

    return render_template('events/edit.html', event=event)



# Delete event
@event_bp.route('/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    # Fetch event to check ownership
    curs.execute('SELECT created_by FROM events WHERE event_id=%s', (event_id,))
    event = curs.fetchone()

    if event is None:
        flash("Event not found.", "warning")
        return redirect(url_for('event_bp.list_events'))

    # Ownership check
    if event['created_by'] != session.get('user_id'):
        flash("You can only delete events you created!", "warning")
        return redirect(url_for('event_bp.list_events'))

    # Delete RSVPs first
    curs.execute('DELETE FROM rsvp WHERE event_id=%s', (event_id,))

    # Delete event
    curs.execute('DELETE FROM events WHERE event_id=%s', (event_id,))
    conn.commit()

    flash("Event and associated RSVPs deleted successfully!")
    return redirect(url_for('event_bp.list_events'))


# RSVP
@event_bp.route('/<int:event_id>/rsvp', methods = ['POST'])
@login_required
def rsvp(event_id):
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    user_id = session.get('user_id', 1)
    created_at = datetime.datetime.now()
    status = request.form.get('status')

    if not status:  # safety check
        flash("Please select an RSVP option.")
        return redirect(url_for('event_bp.event_details', event_id=event_id))

    # Check if the user already RSVPed
    curs.execute('SELECT * FROM rsvp WHERE event_id=%s AND created_by=%s', (event_id, user_id))
    existing = curs.fetchone()

    if existing:
        # Update the existing RSVP
        curs.execute('''
            UPDATE rsvp
            SET status=%s, created_at=%s
            WHERE event_id=%s AND created_by=%s
        ''', (status, created_at, event_id, user_id))
        flash("Your RSVP has been updated.")
    else:
        # Insert new RSVP
        curs.execute('''
            INSERT INTO rsvp(event_id, created_by, status, created_at)
            VALUES (%s, %s, %s, %s)
        ''', (event_id, user_id, status, created_at))
        flash("Your RSVP has been recorded.")

    conn.commit()
    return redirect(url_for('event_bp.event_details', event_id = event_id))
