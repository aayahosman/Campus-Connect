from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from cs304dbi import connect
from auth_utils import login_required
from db import resources_db

resource_bp = Blueprint('resources', __name__, url_prefix='/resources')

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
    return connect()

@resource_bp.route('/')
def list_resources():
    conn = getConn()

    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    resources = resources_db.list_resources(conn, q=q, category=category)
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
    if request.method == 'POST':
        title = request.form['title']
        category = request.form.get('category')  # fixed bug
        description = request.form['description']
        contact_info = request.form.get('contact_info')
        status = request.form.get('status')

        created_by = session.get('user_id')
        if created_by is None:
            flash("You must be logged in to add a resource.", "warning")
            return redirect(url_for('auth.index'))

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

    categories = sorted(RESOURCE_CATEGORIES)
    return render_template('resources/add.html', categories=categories)

@resource_bp.route('/edit/<int:resource_id>', methods=['GET', 'POST'])
@login_required
def edit_resource(resource_id):
    conn = getConn()
    resource = resources_db.get_resource_by_id(conn, resource_id)

    if resource is None:
        flash("Resource not found.", "warning")
        return redirect(url_for('resources.list_resources'))

    if resource['created_by'] != session.get('user_id'):
        flash("You can only edit resources you created!", "warning")
        return redirect(url_for('resources.list_resources'))

    if request.method == 'POST':
        title = request.form['title']
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

    categories = sorted(RESOURCE_CATEGORIES)
    return render_template('resources/edit.html', resource=resource, categories=categories)

@resource_bp.route('/delete/<int:resource_id>', methods=['POST'])
@login_required
def delete_resource(resource_id):
    conn = getConn()

    owner_row = resources_db.get_resource_owner(conn, resource_id)
    if owner_row is None:
        flash("Resource not found.", "warning")
        return redirect(url_for('resources.list_resources'))

    if owner_row['created_by'] != session.get('user_id'):
        flash("You can only delete resources you created!", "warning")
        return redirect(url_for('resources.list_resources'))

    resources_db.delete_resource(conn, resource_id)
    flash("Resource deleted successfully!")
    return redirect(url_for('resources.list_resources'))
