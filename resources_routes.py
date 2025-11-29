from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from cs304dbi import connect
import cs304dbi as dbi
from auth_utils import login_required

resource_bp = Blueprint('resources', __name__, url_prefix='/resources')

def getConn():
    return connect()

# ---- Read ----
@resource_bp.route('/')
def list_resources():
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

    # build category list for dropdown with valid categories, will be edited later to avoid categories that are too similar 
    curs.execute('''
        SELECT DISTINCT category
        FROM resources
        WHERE category IS NOT NULL AND category <> ''
        ORDER BY category
    ''')
    cat_rows = curs.fetchall()
    categories = [row['category'] for row in cat_rows]

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
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
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
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    # Fetch the resource + ownership
    curs.execute('SELECT * FROM resources WHERE resource_id=%s', (resource_id,))
    resource = curs.fetchone()

    # Ownership check (BEFORE any updates)
    if resource['created_by'] != session.get('user_id'):
        flash("You can only edit resources you created!", "warning")
        return redirect(url_for('resources.list_resources'))
    
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
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
    return render_template('resources/edit.html', resource=resource)

# ---- Delete ----
@resource_bp.route('/delete/<int:resource_id>', methods=['POST'])
@login_required
def delete_resource(resource_id):
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
