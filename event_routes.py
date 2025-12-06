from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from cs304dbi import connect
import cs304dbi as dbi
import datetime
from auth_utils import login_required
from flask import jsonify

dbi.conf('cs304jas_db')

event_bp = Blueprint('event_bp', __name__, url_prefix='/events')

#pre defined categories to allow for filters
EVENT_CATEGORIES = [
    "Academic Event",
    "Activism",
    "Basic Needs Support",
    "Career & Professional Development",
    "Civic Engagement",
    "Community Event",
    "Crafts & Creative Activities",
    "Cultural",
    "Food Resources / Food Events",
    "Health & Wellness",
    "Internship & Career Exploration",
    "Research Opportunities",
    "Social",
    "Student Life",
    "Workshops & Training",
]

def getConn():
    return connect()

# Read events

@event_bp.route('/')
def list_events():
    """
    List all events from the database and render them in a template.
    This function establishes a connection to the database, retrieves all events
    ordered by their creation date in descending order, and then renders the 
    events in the specified HTML template.
    Returns:
        Rendered HTML template containing the list of events.
    """

    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    # read search term query string
    q = request.args.get('q', '').strip()
    # get category from args
    category = request.args.get('category', '')

    # base SQL that will be edited later, 1=1 to allow adding on AND's later
    sql = '''
        SELECT *
        FROM events
        WHERE 1=1
    '''
    params = []

    # keyword search over title + description
    if q:
        sql += ' AND (title LIKE %s OR description LIKE %s)'
        like = f"%{q}%"
        params.extend([like, like])

    # category filter if the user decides to add a category aswell 
    if category:
        sql += ' AND category = %s'
        
        params.append(category)

    # sort newest first (or by date_of_event if you prefer)
    sql += ' ORDER BY created_at DESC'

    curs.execute(sql, params)
    events = curs.fetchall()

    # build category list for dropdown with valid categories
    categories = sorted(EVENT_CATEGORIES)

    return render_template(
        'events/list.html',
        events=events,
        q=q,
        categories=categories,
        selected_category=category,
    )

# Add events
@event_bp.route('/add', methods = ['GET', 'POST'])
@login_required
def add_event():
    """
    Adds a new event to the database.
    This function handles the HTTP POST request to create a new event.
    It retrieves event details from the form data, checks if the user is logged in,
    and inserts the event information into the 'events' table in the database.
    Returns:
        Redirects to the event listing page upon successful creation of the event.
        If the user is not logged in, it redirects to the authentication index page.
    Raises:
        Flash messages for user feedback on success or failure conditions.
    """

    conn = getConn()
    curs = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        date_of_event = request.form['date_of_event'] 
        category = request.form['category']
        description = request.form['description']
        contact_info = request.form.get('contact_info')

        address1 = request.form.get('address1')
        address2 = request.form.get('address2')
        city = request.form.get('city')
        state = request.form.get('state')
        postal_code = request.form.get('postal_code')

            
        created_by = session.get('user_id')
        if created_by is None:
            flash("You must be logged in to create events.", "warning")
            return redirect(url_for('auth.index'))

        created_at = datetime.datetime.now()

        curs.execute('''
            INSERT INTO events (
                title,
                date_of_event,
                category,
                created_by,
                created_at,
                description,
                contact_info,
                address1,
                address2,
                city,
                state,
                postal_code
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (title, date_of_event, category,
              created_by, created_at,
              description, contact_info,
              address1, address2, city, state, postal_code))
        conn.commit()
        flash("Event created successfully!")
        return redirect(url_for('event_bp.list_events'))

    return render_template('events/add.html')

# Shows event full details & RSVP
@event_bp.route('/<int:event_id>')
def event_details(event_id):
    """
    Fetches the details of a specific event, including its information, 
    the RSVP statuses of attendees, and the current user's RSVP status. 
    If the event is not found, it redirects to the list of events. 
    Parameters:
        event_id (int): The unique identifier of the event.
    Returns:
        Rendered HTML template with event details, RSVP information, 
        and the user's RSVP status.
    """

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
    """
    Edit an existing event in the database.
    This function retrieves an event by its ID, checks if the user has ownership of the event,
    and allows the user to update the event's details such as title, date, category, description,
    contact information, and address. If the event is not found or the user does not have permission
    to edit it, appropriate warnings are flashed, and the user is redirected to the event list.
    Parameters:
        event_id (int): The unique identifier of the event to be edited.
    Returns:
        Redirects to the event list page after successful update or displays an edit form for the event.
    """

    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    # Fetch the event once
    curs.execute('SELECT * FROM events WHERE event_id=%s', (event_id,))
    event = curs.fetchone()

    if event is None:
        flash("Event not found.", "warning")
        return redirect(url_for('event_bp.list_events'))

    # Ownership check
    # if event['created_by'] != session.get('user_id'):
    #     flash("You can only edit events you created!", "warning")
    #     return redirect(url_for('event_bp.list_events'))

    if request.method == 'POST':
        title = request.form['title']
        date_of_event = request.form['date_of_event']
        category = request.form['category']
        description = request.form['description']
        contact_info = request.form.get('contact_info')

        address1 = request.form.get('address1')
        address2 = request.form.get('address2')
        city = request.form.get('city')
        state = request.form.get('state')
        postal_code = request.form.get('postal_code')

        curs.execute('''
            UPDATE events
            SET
                title         = %s,
                date_of_event = %s,
                category      = %s,
                description   = %s,
                contact_info  = %s,
                address1      = %s,
                address2      = %s,
                city          = %s,
                state         = %s,
                postal_code   = %s
            WHERE event_id = %s
        ''', (title, date_of_event, category,
              description, contact_info,
              address1, address2, city, state, postal_code,
              event_id))

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
    """
    Deletes an event and its associated RSVPs from the database.
    This function first checks if the event exists and if the user attempting to delete it is the owner. 
    If the event is found and the ownership is verified, it deletes all RSVPs associated with the event 
    before finally removing the event itself from the database. 
    Parameters:
        event_id (int): The unique identifier of the event to be deleted.
    Returns:
        Redirects to the event listing page with a flash message indicating the result of the operation.
    """

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
@event_bp.route('/<int:event_id>/rsvp', methods=['POST'])
@login_required
def rsvp(event_id):
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    user_id = session.get('user_id')
    created_at = datetime.datetime.now()
    status = request.form.get('status')

    if not status:
        flash("Please select an RSVP option.")
        return redirect(url_for('event_bp.event_details', event_id=event_id))

    # Check if existing RSVP
    curs.execute(
        'SELECT * FROM rsvp WHERE event_id=%s AND created_by=%s',
        (event_id, user_id)
    )
    existing = curs.fetchone()

    if existing:
        curs.execute('''
            UPDATE rsvp
            SET status=%s, created_at=%s
            WHERE event_id=%s AND created_by=%s
        ''', (status, created_at, event_id, user_id))
        message = "Your RSVP has been updated!"
    else:
        curs.execute('''
            INSERT INTO rsvp(event_id, created_by, status, created_at)
            VALUES (%s, %s, %s, %s)
        ''', (event_id, user_id, status, created_at))
        message = "Your RSVP has been recorded!"

    conn.commit()

    # Reload event + RSVPS so we can show SVG icons + success box
    curs.execute('SELECT * FROM events WHERE event_id=%s', (event_id,))
    event = curs.fetchone()

    curs.execute('''
        SELECT rsvp.status, rsvp.created_at, users.full_name AS name
        FROM rsvp
        JOIN users ON rsvp.created_by = users.user_id
        WHERE rsvp.event_id=%s
        ORDER BY
            CASE rsvp.status WHEN 'yes' THEN 1 WHEN 'maybe' THEN 2 ELSE 3 END,
            created_at ASC
    ''', (event_id,))
    rsvps = curs.fetchall()

    curs.execute('''
        SELECT status
        FROM rsvp
        WHERE event_id=%s AND created_by=%s
    ''', (event_id, user_id))
    user_rsvp = curs.fetchone()

    # render detail.html WITH the "submitted" flag
    return render_template(
        'events/detail.html',
        event=event,
        rsvps=rsvps,
        user_rsvp=user_rsvp,
        submitted=message  # pass the text instead of True
    )

@event_bp.route("/calendar")
def calendar_view():
    return render_template("calendar_view.html")

@event_bp.route('/api/events')
def events_json():
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    curs.execute('''
        SELECT event_id, title, date_of_event, description
        FROM events
        ORDER BY date_of_event ASC
    ''')
    records = curs.fetchall()

    events = []
    for r in records:
        # FullCalendar needs {"title": "...", "start": "..."}
        events.append({
            "id": r["event_id"],
            "title": r["title"],
            "start": r["date_of_event"].isoformat(),
            "description": r["description"]
        })

    return jsonify(events)
