from cs304dbi import connect
import cs304dbi as dbi

def getConn():
    return connect()

# ---- LIST ----
def list_services(q=''):
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)

    sql = 'SELECT * FROM services WHERE 1=1'
    params = []

    if q:
        sql += ' AND (service_name LIKE %s OR description LIKE %s)'
        like = f"%{q}%"
        params.extend([like, like])

    sql += ' ORDER BY created_at DESC'
    curs.execute(sql, params)
    return curs.fetchall()


# ---- GET SINGLE SERVICE ----
def get_service(service_id):
    conn = getConn()
    curs = conn.cursor(dbi.dictCursor)
    curs.execute('SELECT * FROM services WHERE service_id=%s', (service_id,))
    return curs.fetchone()


# ---- ADD ----
def add_service(data):
    conn = getConn()
    curs = conn.cursor()
    curs.execute('''
        INSERT INTO services (service_name, category, description, price_range,
                              service_location_type, availability, contact_method,
                              created_by, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
    ''', (data['service_name'], data['category'], data['description'],
          data['price_range'], data['location_type'], data['availability'],
          data['contact_method'], data['created_by']))
    conn.commit()


# ---- UPDATE ----
def update_service(service_id, data):
    conn = getConn()
    curs = conn.cursor()
    curs.execute('''
        UPDATE services
        SET service_name=%s, category=%s, description=%s, price_range=%s,
            service_location_type=%s, availability=%s, contact_method=%s
        WHERE service_id=%s
    ''', (data['service_name'], data['category'], data['description'], data['price_range'],
          data['location_type'], data['availability'], data['contact_method'], service_id))
    conn.commit()


# ---- DELETE ----
def delete_service(service_id):
    conn = getConn()
    curs = conn.cursor()
    curs.execute('DELETE FROM services WHERE service_id=%s', (service_id,))
    conn.commit()
