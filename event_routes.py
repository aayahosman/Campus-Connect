from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from cs304dbi import connect
import datetime
from auth_utils import login_required
from db import event_db
import cs304dbi as dbi

# Configure database connection for this blueprint/module
dbi.conf('cs304jas_db')

event_bp = Blueprint('event_bp', __name__, url_prefix='/events')

# Predefined categories for events
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
    """Return a database connection."""
    return connect()


@event_bp.route('/')
def list_events():
    """
    Display the list of events, optionally filtered by
    a search query and/or category.
    """
    conn = getConn()

    # Read optional query parameters for filtering:
    # - q: free-text search
    # - category: restrict to a specific event category
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    # Fetch events applying any provided filters
    events = event_db.list_events(conn, q=q, category=category)

    # Sort categories for consistent display in the UI
    categories = sorted(EVENT_CATEGORIES)

    return render_template(
        'events/list.html',
        events=events,
        q=q,
        categories=categories,
        selected_category=category,
    )


@event_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_event():
    """
    Show the add-event form (GET) or create a new event (POST).
    Only accessible to logged-in users.
    """
    # POST: process the submitted add-event form
    if request.method == 'POST':
        # Collect required form fields
        title = request.form['title']
        date_of_event = request.form['date_of_event']
        category = request.form.get('category')
        description = request.form['description']
        contact_info = request.form.get('contact_info')

        # Collect optional location fields (may be blank)
        address1 = request.form.get('address1')
        address2 = request.form.get('address2')
        city = request.form.get('city')
        state = request.form.get('state')
        postal_code = request.form.get('postal_code')

        # Associate the event with the currently logged-in user
        created_by = session.get('user_id')
        if created_by is None:
            # Defensive fallback in case session state is lost
            flash("You must be logged in to create events.", "warning")
            return redirect(url_for('auth.index'))

        # Timestamp the creation (useful for sorting/auditing)
        created_at = datetime.datetime.now()

        # Insert the new event into the database
        conn = getConn()
        event_db.insert_event(
            conn,
            title=title,
            date_of_event=date_of_event,
            category=category,
            created_by=created_by,
            created_at=created_at,
            description=description,
            contact_info=contact_info,
            address1=address1,
            address2=address2,
            city=city,
            state=state,
            postal_code=postal_code
        )

        flash("Event created successfully!")
        return redirect(url_for('event_bp.list_events'))

    # GET: show the add-event form
    categories = sorted(EVENT_CATEGORIES)
    return render_template('events/add.html', categories=categories)


@event_bp.route('/<int:event_id>')
def event_details(event_id):
    """
    Display a single event's details page, including RSVP information
    and the current user's RSVP status (if logged in).
    """
    conn = getConn()

    # Load the event and redirect if it does not exist
    event = event_db.get_event_by_id(conn, event_id)
    if event is None:
        flash("Event not found.")
        return redirect(url_for('event_bp.list_events'))

    # Fetch RSVPs to display (typically only YES/MAYBE)
    rsvps = event_db.list_rsvps_yes_maybe(conn, event_id)

    # If the user is logged in, fetch their RSVP status for this event
    user_id = session.get('user_id')
    user_rsvp = None
    if user_id is not None:
        user_rsvp = event_db.get_user_rsvp(conn, event_id, user_id)

    return render_template(
        'events/detail.html',
        event=event,
        rsvps=rsvps,
        user_rsvp=user_rsvp
    )


@event_bp.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    """
    Edit an existing event. Only the creator of the event
    is allowed to make changes.
    """
    conn = getConn()

    # Load the event to edit
    event = event_db.get_event_by_id(conn, event_id)
    if event is None:
        flash("Event not found.", "warning")
        return redirect(url_for('event_bp.list_events'))

    # Ownership check to prevent unauthorized edits
    if event['created_by'] != session.get('user_id'):
        flash("You can only edit events you created!", "warning")
        return redirect(url_for('event_bp.list_events'))

    # POST: update the event with submitted form data
    if request.method == 'POST':
        title = request.form['title']
        date_of_event = request.form['date_of_event']
        # Preserve existing category if the user does not select one
        category = request.form.get('category') or event['category']
        description = request.form['description']
        contact_info = request.form.get('contact_info')

        # Collect optional location fields (may be blank)
        address1 = request.form.get('address1')
        address2 = request.form.get('address2')
        city = request.form.get('city')
        state = request.form.get('state')
        postal_code = request.form.get('postal_code')

        event_db.update_event(
            conn,
            event_id=event_id,
            title=title,
            date_of_event=date_of_event,
            category=category,
            description=description,
            contact_info=contact_info,
            address1=address1,
            address2=address2,
            city=city,
            state=state,
            postal_code=postal_code
        )

        flash("Event updated successfully!")
        return redirect(url_for('event_bp.list_events'))

    # GET: pre-fill the edit form. Convert datetime to input-friendly format.
    if event.get('date_of_event') and hasattr(event['date_of_event'], "strftime"):
        event['date_of_event'] = event['date_of_event'].strftime('%Y-%m-%dT%H:%M')

    categories = sorted(EVENT_CATEGORIES)
    return render_template('events/edit.html', event=event, categories=categories)


@event_bp.route('/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    """
    Delete an event and its associated RSVPs.
    Only the creator of the event may delete it.
    """
    conn = getConn()

    # Fetch owner information to verify permissions
    owner_row = event_db.get_event_owner(conn, event_id)
    if owner_row is None:
        flash("Event not found.", "warning")
        return redirect(url_for('event_bp.list_events'))

    # Enforce ownership before deletion
    if owner_row['created_by'] != session.get('user_id'):
        flash("You can only delete events you created!", "warning")
        return redirect(url_for('event_bp.list_events'))

    # Delete the event and any RSVP rows referencing it
    event_db.delete_event_and_rsvps(conn, event_id)
    flash("Event and associated RSVPs deleted successfully!")
    return redirect(url_for('event_bp.list_events'))


@event_bp.route('/<int:event_id>/rsvp', methods=['POST'])
@login_required
def rsvp(event_id):
    """
    Create or update the current user's RSVP for an event.
    Requires the user to be logged in.
    """
    conn = getConn()

    user_id = session.get('user_id')
    created_at = datetime.datetime.now()
    status = request.form.get('status')

    # Basic validation: ensure a status was chosen
    if not status:
        flash("Please select an RSVP option.")
        return redirect(url_for('event_bp.event_details', event_id=event_id))

    # Upsert behavior: update if RSVP exists, otherwise insert a new one
    existing = event_db.get_existing_rsvp(conn, event_id, user_id)
    if existing:
        event_db.update_rsvp(conn, event_id, user_id, status, created_at)
        message = "Your RSVP has been updated!"
    else:
        event_db.insert_rsvp(conn, event_id, user_id, status, created_at)
        message = "Your RSVP has been recorded!"

    # Reload event + RSVPs for display (keeps current behavior)
    event = event_db.get_event_by_id(conn, event_id)
    rsvps = event_db.list_rsvps_yes_maybe(conn, event_id)
    user_rsvp = event_db.get_user_rsvp(conn, event_id, user_id)

    return render_template(
        'events/detail.html',
        event=event,
        rsvps=rsvps,
        user_rsvp=user_rsvp,
        submitted=message
    )


@event_bp.route("/calendar")
def calendar_view():
    """Render the calendar page (front-end loads event data via /api/events)."""
    return render_template("calendar_view.html")


@event_bp.route('/api/events')
def events_json():
    """
    Return event data as JSON for the calendar UI.
    Includes id, title, start time, and a short description.
    """
    conn = getConn()

    # Fetch lightweight event records for calendar rendering
    records = event_db.list_events_for_calendar(conn)

    # Convert database records into the JSON shape expected by the front end
    events = []
    for r in records:
        events.append({
            "id": r["event_id"],
            "title": r["title"],
            "start": r["date_of_event"].isoformat() if r["date_of_event"] else None,
            "description": r["description"]
        })

    return jsonify(events)
