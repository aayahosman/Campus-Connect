from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session, jsonify,
    current_app
)
import cs304dbi as dbi
import datetime
import os
from werkzeug.utils import secure_filename

from auth_utils import login_required
from db import event_db
from PIL import Image

dbi.conf('cs304jas_db')

event_bp = Blueprint('event_bp', __name__, url_prefix='/events')

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
    "Other"
]


def getConn():
    return dbi.connect()


@event_bp.route('/')
def list_events():
    conn = getConn()
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    events = event_db.list_events(conn, q=q, category=category)
    categories = sorted(EVENT_CATEGORIES)

    return render_template(
        'events/list.html',
        events=events,
        q=q,
        categories=categories,
        selected_category=category
    )


@event_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_event():
    if request.method == 'POST':
        conn = getConn()

        title = request.form['title']
        date_of_event = request.form['date_of_event']
        category = request.form.get('category')
        description = request.form['description']
        contact_info = request.form.get('contact_info')

        address1 = request.form.get('address1')
        address2 = request.form.get('address2')
        city = request.form.get('city')
        state = request.form.get('state')
        postal_code = request.form.get('postal_code')

        created_by = session['user_id']
        created_at = datetime.datetime.now()

        event_id = event_db.insert_event(
            conn,
            title, date_of_event, category,
            created_by, created_at,
            description, contact_info,
            address1, address2, city, state, postal_code
        )

        file = request.files.get('image')
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                flash("Invalid image type.")
                return redirect(url_for('event_bp.add_event'))

            # Validate actual image content
            try:
                Image.open(file).verify()
                file.seek(0)  
            except Exception:
                flash("Uploaded file is not a valid image.")
                return redirect(url_for('event_bp.add_event'))

            filename = secure_filename(f"event_{event_id}.{ext}")
            path = os.path.join(current_app.config['UPLOADS'], filename)

            file.save(path)
            os.chmod(path, 0o644)

            curs = conn.cursor()
            curs.execute(
                "UPDATE events SET image_filename=%s WHERE event_id=%s",
                (filename, event_id)
            )
            conn.commit()

        flash("Event created successfully!")
        return redirect(url_for('event_bp.list_events'))

    categories = sorted(EVENT_CATEGORIES)
    return render_template('events/add.html', categories=categories)


@event_bp.route('/<int:event_id>')
def event_details(event_id):
    conn = getConn()
    event = event_db.get_event_by_id(conn, event_id)

    if not event:
        flash("Event not found.")
        return redirect(url_for('event_bp.list_events'))

    rsvps = event_db.list_rsvps_yes_maybe(conn, event_id)

    user_rsvp = None
    if 'user_id' in session:
        user_rsvp = event_db.get_user_rsvp(conn, event_id, session['user_id'])

    return render_template(
        'events/detail.html',
        event=event,
        rsvps=rsvps,
        user_rsvp=user_rsvp
    )


@event_bp.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    conn = getConn()
    event = event_db.get_event_by_id(conn, event_id)

    if not event:
        flash("Event not found.")
        return redirect(url_for('event_bp.list_events'))

    if event['created_by'] != session['user_id']:
        flash("You can only edit events you created.")
        return redirect(url_for('event_bp.list_events'))

    if request.method == 'POST':
        event_db.update_event(
            conn,
            event_id,
            request.form['title'],
            request.form['date_of_event'],
            request.form.get('category') or event['category'],
            request.form['description'],
            request.form.get('contact_info'),
            request.form.get('address1'),
            request.form.get('address2'),
            request.form.get('city'),
            request.form.get('state'),
            request.form.get('postal_code')
        )

        file = request.files.get('image')
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                flash("Invalid image type.")
                return redirect(url_for('event_bp.edit_event', event_id=event_id))

            # Validate actual image content
            try:
                Image.open(file).verify()
                file.seek(0)  
            except Exception:
                flash("Uploaded file is not a valid image.")
                return redirect(url_for('event_bp.edit_event', event_id=event_id))

            filename = secure_filename(f"event_{event_id}.{ext}")
            path = os.path.join(current_app.config['UPLOADS'], filename)

            file.save(path)
            os.chmod(path, 0o644)

            curs = conn.cursor()
            curs.execute(
                "UPDATE events SET image_filename=%s WHERE event_id=%s",
                (filename, event_id)
            )
            conn.commit()

        flash("Event updated successfully!")
        return redirect(url_for('event_bp.list_events'))

    if event.get('date_of_event'):
        event['date_of_event'] = event['date_of_event'].strftime('%Y-%m-%dT%H:%M')

    for field in ['address1', 'address2', 'city', 'state', 'postal_code']:
        if event.get(field) is None:
            event[field] = ''

    categories = sorted(EVENT_CATEGORIES)
    return render_template('events/edit.html', event=event, categories=categories)


@event_bp.route('/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    conn = getConn()
    owner = event_db.get_event_owner(conn, event_id)

    if not owner:
        flash("Event not found.")
        return redirect(url_for('event_bp.list_events'))

    if owner['created_by'] != session['user_id']:
        flash("You can only delete events you created.")
        return redirect(url_for('event_bp.list_events'))

    event_db.delete_event_and_rsvps(conn, event_id)
    flash("Event deleted.")
    return redirect(url_for('event_bp.list_events'))


@event_bp.route('/<int:event_id>/rsvp', methods=['POST'])
@login_required
def rsvp(event_id):
    conn = getConn()
   
    event = event_db.get_event_by_id(conn, event_id)
    if not event:
        flash("This event no longer exists.")
        return redirect(url_for("event_bp.list_events"))

    user_id = session['user_id']
    status = request.form.get('status')

    if not status:
        flash("Please choose an RSVP option.")
        return redirect(url_for('event_bp.event_details', event_id=event_id))

    created_at = datetime.datetime.now()
    existing = event_db.get_existing_rsvp(conn, event_id, user_id)

    if existing:
        event_db.update_rsvp(conn, event_id, user_id, status, created_at)
    else:
        event_db.insert_rsvp(conn, event_id, user_id, status, created_at)

    return redirect(url_for('event_bp.event_details', event_id=event_id))


@event_bp.route('/api/events')
def events_json():
    conn = getConn()
    records = event_db.list_events_for_calendar(conn)

    return jsonify([
        {
            "id": r["event_id"],
            "title": r["title"],
            "start": r["date_of_event"].isoformat() if r["date_of_event"] else None,
            "description": r["description"]
        }
        for r in records
    ])

@event_bp.route('/calendar')
def calendar_view():
    return render_template('calendar_view.html')