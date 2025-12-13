from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from cs304dbi import connect
import cs304dbi as dbi
from auth_utils import login_required

resource_bp = Blueprint('resources', __name__, url_prefix='/resources')
#predefine categories 
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

# ---- Read ----
@resource_bp.route('/')
def list_resources():
    """
    Fetches a list of resources from the database and renders them in a template.
    This function connects to the database, retrieves all resources ordered by their 
    creation date in descending order, and then passes the retrieved resources to 
    the 'resources/list.html' template for rendering.
    Returns:
        Rendered HTML template displaying the list of resources.
    """

    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    # search term and selected category from query string
    q = request.args.get('q', '').strip()
    #get the categories from the user
    category = request.args.get('category', '')

    # base SQL that will be edited later, 1=1 to allow adding on AND's later
    sql = '''
        SELECT *
        FROM resources
        WHERE 1=1
    '''
    params = []

    # keyword search
    if q:
        sql += ' AND (title LIKE %s OR description LIKE %s OR category LIKE %s)'
        like = f"%{q}%"
        params.extend([like, like, like])

    # category filter if the user decides to add a category aswell 
    if category:
        sql += ' AND category = %s'
        params.append(category)

    sql += ' ORDER BY created_at DESC'

    curs.execute(sql, params)
    resources = curs.fetchall()

    # build category list for dropdown with valid categories,
    categories = sorted(RESOURCE_CATEGORIES)


    return render_template(
        'resources/list.html',
        resources=resources,
        q=q,
        categories=categories,
        selected_category=category,
    )


# ---- Create ----
@resource_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_resource():
    """
    Adds a new resource to the database.
    This function handles the POST request to add a resource, extracting the necessary
    information from the form data, and inserting it into the 'resources' table. It also
    records the user who created the resource and sets the creation timestamp. Upon
    successful addition, it flashes a success message and redirects the user to the
    list of resources. If the request method is not POST, it renders the add resource
    template.
    Returns:
        Redirects to the resource list page upon successful addition or renders the
        add resource template for GET requests.
    """

    if request.method == 'POST':
        title = request.form['title']
        category = request.form.get('category') or category['category']

        description = request.form['description']
        contact_info = request.form['contact_info']
        status = request.form['status']

        conn = getConn()
        curs = conn.cursor()
        created_by = session.get('user_id')
        curs.execute('''
        INSERT INTO resources (title, category, description, contact_info, status, created_by, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ''', (title, category, description, contact_info, status, created_by))
        conn.commit()
        flash("Resource added successfully!")
        return redirect(url_for('resources.list_resources'))
    return render_template('resources/add.html')

# ---- Update ----
@resource_bp.route('/edit/<int:resource_id>', methods=['GET', 'POST'])
@login_required
def edit_resource(resource_id):
    """
    Edit a resource in the database.
    This function allows a user to edit an existing resource if they are the creator of that resource. 
    It first checks the ownership of the resource and then processes the update if the request method 
    is POST. If the user is not the creator, a warning message is flashed, and the user is redirected 
    to the list of resources. If the resource is successfully updated, a success message is flashed.
    Parameters:
        resource_id (int): The ID of the resource to be edited.
    Returns:
        Redirects to the list of resources or renders the edit resource template.
    """

    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    # Fetch the resource + ownership
    curs.execute('SELECT * FROM resources WHERE resource_id=%s', (resource_id,))
    resource = curs.fetchone()

    # # Ownership check (BEFORE any updates)
    if resource['created_by'] != session.get('user_id'):
        flash("You can only edit resources you created!", "warning")
        return redirect(url_for('resources.list_resources'))
    
    if request.method == 'POST':
        title = request.form['title']
       
        category = request.form.get('category') or resource['category']

        description = request.form['description']
        contact_info = request.form['contact_info']
        status = request.form['status']
        curs.execute('''
            UPDATE resources
            SET title=%s, category=%s, description=%s, contact_info=%s, status=%s
            WHERE resource_id=%s
        ''', (title, category, description, contact_info, status, resource_id))
        conn.commit()
        flash("Resource updated successfully!")
        return redirect(url_for('resources.list_resources'))

    curs.execute('SELECT * FROM resources WHERE resource_id=%s', (resource_id,))
    resource = curs.fetchone()
    return render_template('resources/edit.html', resource=resource, )

# ---- Delete ----
@resource_bp.route('/delete/<int:resource_id>', methods=['POST'])
@login_required
def delete_resource(resource_id):
    """
    Deletes a resource from the database if the current user is the owner.
    This function checks if the user attempting to delete the resource is the 
    creator of that resource. If the user is not the owner, a warning message 
    is flashed, and the user is redirected to the list of resources. If the 
    user is the owner, the resource is deleted from the database, a success 
    message is flashed, and the user is redirected to the list of resources.
    Parameters:
        resource_id (int): The ID of the resource to be deleted.
    Returns:
        Redirect: A redirect response to the resources list page.
    """

    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    # Fetch resource owner
    curs.execute('SELECT created_by FROM resources WHERE resource_id=%s', [resource_id])
    resource = curs.fetchone()

    # Ownership check
    if resource['created_by'] != session.get('user_id'):
        flash("You can only delete resources you created!", "warning")
        return redirect(url_for('resources.list_resources'))
    
    curs.execute('DELETE FROM resources WHERE resource_id=%s', (resource_id,))
    conn.commit()
    flash("Resource deleted successfully!")
    return redirect(url_for('resources.list_resources'))
