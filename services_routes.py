from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth_utils import login_required
from cs304dbi import connect
from db import services_db

services_bp = Blueprint('services', __name__, url_prefix='/services')

SERVICE_CATEGORIES = [
    "Beauty & Personal Care",
    "Tutoring & Academic Support",
    "Wellness & Fitness",
    "Career & Professional Services",
    "Creative Services",
    "Technology & Digital Help",
    "Event & Campus Services",
    "Home & Lifestyle Services",
    "Errands & Task Help",
    "Other"
]

def getConn():
    return connect()

@services_bp.route('/')
def list_services():
    conn = getConn()

    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    services = services_db.list_services(conn, q=q, category=category)
    categories = sorted(SERVICE_CATEGORIES)

    return render_template(
        'services/list.html',
        services=services,
        q=q,
        categories=categories,
        selected_category=category,
    )

@services_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_service():
    if request.method == 'POST':
        service_name = request.form['service_name']
        category = request.form.get('category', None)
        description = request.form['description']
        price_range = request.form['price_range']
        location_type = request.form['service_location_type']
        availability = request.form['availability']
        contact_method = request.form['contact_method']

        created_by = session.get('user_id')
        if created_by is None:
            flash("You must be logged in to add a service.", "warning")
            return redirect(url_for('auth.index'))

        conn = getConn()
        services_db.insert_service(
            conn,
            service_name=service_name,
            category=category,
            description=description,
            price_range=price_range,
            location_type=location_type,
            availability=availability,
            contact_method=contact_method,
            created_by=created_by
        )

        flash("Service added successfully!")
        return redirect(url_for('services.list_services'))

    categories = sorted(SERVICE_CATEGORIES)
    return render_template("services/add.html", categories=categories)

@services_bp.route('/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
def edit_service(service_id):
    conn = getConn()
    service = services_db.get_service_by_id(conn, service_id)

    if service is None:
        flash("Service not found.", "warning")
        return redirect(url_for('services.list_services'))

    if service['created_by'] != session.get('user_id'):
        flash("You can only edit services you created!", "warning")
        return redirect(url_for('services.list_services'))

    if request.method == 'POST':
        service_name = request.form['service_name']
        category = request.form.get('category', None)
        description = request.form['description']
        price_range = request.form['price_range']
        location_type = request.form['service_location_type']
        availability = request.form['availability']
        contact_method = request.form['contact_method']

        services_db.update_service(
            conn,
            service_id=service_id,
            service_name=service_name,
            category=category,
            description=description,
            price_range=price_range,
            location_type=location_type,
            availability=availability,
            contact_method=contact_method
        )

        flash("Service updated successfully!")
        return redirect(url_for('services.list_services'))

    categories = sorted(SERVICE_CATEGORIES)
    return render_template("services/edit.html", service=service, categories=categories)

@services_bp.route('/delete/<int:service_id>', methods=['POST'])
@login_required
def delete_service(service_id):
    conn = getConn()

    owner_row = services_db.get_service_owner(conn, service_id)
    if owner_row is None:
        flash("Service not found.", "warning")
        return redirect(url_for('services.list_services'))

    if owner_row['created_by'] != session.get('user_id'):
        flash("You can only delete your own services!", "warning")
        return redirect(url_for('services.list_services'))

    services_db.delete_service(conn, service_id)
    flash("Service deleted successfully!")
    return redirect(url_for('services.list_services'))
