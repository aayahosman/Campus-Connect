from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth_utils import login_required
from cs304dbi import connect
import cs304dbi as dbi

services_bp = Blueprint('services', __name__, url_prefix='/services')

def getConn():
    return connect()


@services_bp.route('/')
def list_services():
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    sql = 'SELECT * FROM services WHERE 1=1'
    params = []

    if q:
        sql += ' AND (service_name LIKE %s OR description LIKE %s)'
        like = f"%{q}%"
        params.extend([like, like])

    if category:
        sql += ' AND category LIKE %s'
        params.append(f"%{category}%")

    sql += ' ORDER BY created_at DESC'
    curs.execute(sql, params)
    services = curs.fetchall()

    return render_template('services/list.html',
                           services=services,
                           q=q,
                           category=category)


# ---- Add ----
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

        conn = getConn()
        curs = conn.cursor()
        created_by = session.get('user_id')

        curs.execute('''
            INSERT INTO services (
                service_name, category, description, price_range,
                service_location_type, availability, contact_method,
                created_by, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ''', (service_name, category, description, price_range,
              location_type, availability, contact_method, created_by))
        conn.commit()
        flash("Service added successfully!")
        return redirect(url_for('services.list_services'))

    return render_template('services/add.html')


# ---- Edit ----
@services_bp.route('/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
def edit_service(service_id):
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    curs.execute('SELECT * FROM services WHERE service_id=%s', (service_id,))
    service = curs.fetchone()

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

        curs.execute('''
            UPDATE services
            SET service_name=%s, category=%s, description=%s, price_range=%s,
                service_location_type=%s, availability=%s, contact_method=%s
            WHERE service_id=%s
        ''', (service_name, category, description, price_range,
              location_type, availability, contact_method, service_id))
        conn.commit()
        flash("Service updated successfully!")
        return redirect(url_for('services.list_services'))

    return render_template('services/edit.html', service=service)


# ---- Delete ----
@services_bp.route('/delete/<int:service_id>', methods=['POST'])
@login_required
def delete_service(service_id):
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    curs.execute('SELECT created_by FROM services WHERE service_id=%s', (service_id,))
    service = curs.fetchone()

    if service['created_by'] != session.get('user_id'):
        flash("You can only delete your own services!", "warning")
        return redirect(url_for('services.list_services'))

    curs.execute('DELETE FROM services WHERE service_id=%s', (service_id,))
    conn.commit()
    flash("Service deleted successfully!")
    return redirect(url_for('services.list_services'))
