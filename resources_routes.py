from flask import Blueprint, render_template, request, redirect, url_for, flash
from cs304dbi import connect
import cs304dbi as dbi

resource_bp = Blueprint('resources', __name__, url_prefix='/resources')

def getConn():
    return connect()

# ---- Read ----
@resource_bp.route('/')
def list_resources():
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)
    curs.execute('SELECT * FROM resources ORDER BY created_at DESC')
    resources = curs.fetchall()
    return render_template('resources/list.html', resources=resources)

# ---- Create ----
@resource_bp.route('/add', methods=['GET', 'POST'])
def add_resource():
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        description = request.form['description']
        contact_info = request.form['contact_info']
        status = request.form['status']

        conn = getConn()
        curs = conn.cursor()
        curs.execute('''
            INSERT INTO resources (title, category, description, contact_info, status, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ''', (title, category, description, contact_info, status, 1))
        conn.commit()
        flash("Resource added successfully!")
        return redirect(url_for('resources.list_resources'))
    return render_template('resources/add.html')

# ---- Update ----
@resource_bp.route('/edit/<int:resource_id>', methods=['GET', 'POST'])
def edit_resource(resource_id):
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)
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
def delete_resource(resource_id):
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)
    curs.execute('DELETE FROM resources WHERE resource_id=%s', (resource_id,))
    conn.commit()
    flash("Resource deleted successfully!")
    return redirect(url_for('resources.list_resources'))
