from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from cs304dbi import connect
from auth_utils import login_required
from db import resources_db

resource_bp = Blueprint('resources', __name__, url_prefix='/resources')

# Predefined categories for campus resources
RESOURCE_CATEGORIES = [
    "Academic Support",
    "Basic Needs",
    "Career & Professional Development",
    "Community Programs",
    "Emergency Services",
    "Financial Assistance",
    "Food Assistance",
    "Health and Wellness",
    "Housing Support",
    "Legal Support",
    "Material Assistance",
    "Mental Health",
    "Other",
    "Student Life & Recreation",
    "Technology Resources",
    "Transportation"
]


def getConn():
    """Return a database connection."""
    return connect()


@resource_bp.route('/')
def list_resources():
    """
    Display the list of community resources, optionally filtered
    by a search query and/or category.
    """
    conn = getConn()

    # Read optional query parameters for filtering:
    # - q: free-text search
    # - category: restrict to a specific resource category
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    # Fetch resources from the database applying any provided filters
    resources = resources_db.list_resources(conn, q=q, category=category)

    # Sort categories for consistent display in the UI
    categories = sorted(RESOURCE_CATEGORIES)

    return render_template(
        'resources/list.html',
        resources=resources,
        q=q,
        categories=categories,
        selected_category=category,
    )


@resource_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_resource():
    """
    Show the add-resource form (GET) or create a new resource (POST).
    Only accessible to logged-in users.
    """
    # POST: process the submitted add-resource form
    if request.method == 'POST':
        # Collect required form fields
        title = request.form['title']
        category = request.form.get('category')
        description = request.form['description']
        contact_info = request.form.get('contact_info')
        status = request.form.get('status')

        # Associate the resource with the currently logged-in user
        created_by = session.get('user_id')
        if created_by is None:
            # Defensive fallback in case session state is lost
            flash("You must be logged in to add a resource.", "warning")
            return redirect(url_for('auth.index'))

        # Insert the new resource into the database
        conn = getConn()
        resources_db.insert_resource(
            conn,
            title=title,
            category=category,
            description=description,
            contact_info=contact_info,
            status=status,
            created_by=created_by
        )

        flash("Resource added successfully!")
        return redirect(url_for('resources.list_resources'))

    # GET: show the add-resource form
    categories = sorted(RESOURCE_CATEGORIES)
    return render_template('resources/add.html', categories=categories)


@resource_bp.route('/edit/<int:resource_id>', methods=['GET', 'POST'])
@login_required
def edit_resource(resource_id):
    """
    Edit an existing resource. Only the creator of the resource
    is allowed to make changes.
    """
    conn = getConn()

    # Load the resource to edit
    resource = resources_db.get_resource_by_id(conn, resource_id)
    if resource is None:
        flash("Resource not found.", "warning")
        return redirect(url_for('resources.list_resources'))

    # Ownership check to prevent unauthorized edits
    if resource['created_by'] != session.get('user_id'):
        flash("You can only edit resources you created!", "warning")
        return redirect(url_for('resources.list_resources'))

    # POST: update the resource with submitted form data
    if request.method == 'POST':
        title = request.form['title']
        # Preserve existing category if the user does not select one
        category = request.form.get('category') or resource['category']
        description = request.form['description']
        contact_info = request.form.get('contact_info')
        status = request.form.get('status')

        resources_db.update_resource(
            conn,
            resource_id=resource_id,
            title=title,
            category=category,
            description=description,
            contact_info=contact_info,
            status=status
        )

        flash("Resource updated successfully!")
        return redirect(url_for('resources.list_resources'))

    # GET: show the edit form pre-filled with current resource data
    categories = sorted(RESOURCE_CATEGORIES)
    return render_template('resources/edit.html', resource=resource, categories=categories)


@resource_bp.route('/delete/<int:resource_id>', methods=['POST'])
@login_required
def delete_resource(resource_id):
    """
    Delete a resource. Only the creator of the resource may delete it.
    """
    conn = getConn()

    # Fetch owner information to verify permissions
    owner_row = resources_db.get_resource_owner(conn, resource_id)
    if owner_row is None:
        flash("Resource not found.", "warning")
        return redirect(url_for('resources.list_resources'))

    # Enforce ownership before deletion
    if owner_row['created_by'] != session.get('user_id'):
        flash("You can only delete resources you created!", "warning")
        return redirect(url_for('resources.list_resources'))

    # Perform the delete operation
    resources_db.delete_resource(conn, resource_id)
    flash("Resource deleted successfully!")
    return redirect(url_for('resources.list_resources'))
