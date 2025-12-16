from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth_utils import login_required

import cs304dbi as dbi
from db import services_db

def getConn():
    """Return a database connection."""
    return dbi.connect()

services_bp = Blueprint('services', __name__, url_prefix='/services')

# Predefined categories for services
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



@services_bp.route('/')
def list_services():
    """
    Display the list of services, optionally filtered by
    a search query and/or category.
    """
    conn = getConn()

    # Read optional query parameters used for filtering:
    # - q: free-text search
    # - category: restrict to a specific service category
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    # Fetch services applying any provided filters
    services = services_db.list_services(conn, q=q, category=category)

    # Sort categories for consistent display in the UI
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
    """
    Show the add-service form (GET) or create a new service (POST).
    Only accessible to logged-in users.
    """
    # POST: process the submitted add-service form
    if request.method == 'POST':
        # Collect required form fields
        service_name = request.form['service_name']
        category = request.form.get('category', None)
        description = request.form['description']
        price_range = request.form['price_range']
        location_type = request.form['service_location_type']
        availability = request.form['availability']
        contact_method = request.form['contact_method']

        # Associate the service with the currently logged-in user
        created_by = session.get('user_id')
        if created_by is None:
            # Defensive fallback in case session state is lost
            flash("You must be logged in to add a service.", "warning")
            return redirect(url_for('auth.index'))

        # Insert the new service into the database
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

    # GET: show the add-service form
    categories = sorted(SERVICE_CATEGORIES)
    return render_template("services/add.html", categories=categories)


@services_bp.route('/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
def edit_service(service_id):
    """
    Edit an existing service. Only the creator of the service
    is allowed to make changes.
    """
    conn = getConn()

    # Load the service to edit
    service = services_db.get_service_by_id(conn, service_id)
    if service is None:
        flash("Service not found.", "warning")
        return redirect(url_for('services.list_services'))

    # Ownership check to prevent unauthorized edits
    if service['created_by'] != session.get('user_id'):
        flash("You can only edit services you created!", "warning")
        return redirect(url_for('services.list_services'))

    # POST: update the service with submitted form data
    if request.method == 'POST':
        service_name = request.form['service_name']
        # Preserve existing category if the user does not select one
        category = request.form.get('category') or service['category']
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

    # GET: show the edit form pre-filled with current service data
    categories = sorted(SERVICE_CATEGORIES)
    return render_template("services/edit.html", service=service, categories=categories)


@services_bp.route('/delete/<int:service_id>', methods=['POST'])
@login_required
def delete_service(service_id):
    """
    Delete a service. Only the creator of the service may delete it.
    """
    conn = getConn()

    # Fetch owner information to verify permissions
    owner_row = services_db.get_service_owner(conn, service_id)
    if owner_row is None:
        flash("Service not found.", "warning")
        return redirect(url_for('services.list_services'))

    # Enforce ownership before deletion
    if owner_row['created_by'] != session.get('user_id'):
        flash("You can only delete your own services!", "warning")
        return redirect(url_for('services.list_services'))

    # Perform the delete operation
    services_db.delete_service(conn, service_id)
    flash("Service deleted successfully!")
    return redirect(url_for('services.list_services'))
