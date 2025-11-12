import cs304dbi as dbi

dbi.conf('cs304jas_db')
conn = dbi.connect()
curs = conn.cursor()

curs.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id int PRIMARY KEY auto_increment,
    full_name varchar(80) NOT NULL,
    email varchar(120) UNIQUE,
    password char(12),
    role enum('student','admin')
)
             ''')

curs.execute('''
CREATE TABLE IF NOT EXISTS events (
    event_id int PRIMARY KEY auto_increment,
    title varchar(140),
    date_of_event datetime,
    created_by int,
    created_at datetime,
    description text NOT NULL,
    address1 varchar(120),
    address2 varchar(120),
    city varchar(60),
    state char(2),
    postal_code varchar(10)
    FOREIGN KEY (created_by) REFERENCES users(user_id)
)
             ''')

curs.execute('''
CREATE TABLE IF NOT EXISTS resources (
    resource_id int PRIMARY KEY auto_increment,
    title varchar(140),
    description text NOT NULL,
    category varchar(100),
    contact_info varchar(120),
    status enum('active','inactive'),
    created_by int,
    created_at datetime,
    address1 varchar(120),
    address2 varchar(120),
    city varchar(60),
    state char(2),
    postal_code` varchar(10)
    FOREIGN KEY (created_by) REFERENCES users(user_id)
)
                ''')

curs.execute('''
CREATE TABLE IF NOT EXISTS comments (
    comment_id int PRIMARY KEY auto_increment,
    content text NOT NULL,
    event_id int,
    resource_id int,
    created_by int,
    created_at datetime,
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
    FOREIGN KEY (created_by) REFERENCES users(user_id)
)
                ''')

curs.execute('''
CREATE TABLE rsvp (
    rsvp_id int PRIMARY KEY auto_increment,
    status enum('yes','no','maybe'),
    event_id int,
    created_by int,
    created_at datetime
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
)
                ''')

conn.commit()
curs.close()
conn.close()
