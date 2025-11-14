import cs304dbi as dbi

dbi.conf('cs304jas_db')     # use your database
conn = dbi.connect()
curs = conn.cursor()

curs.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(80) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash CHAR(60) NOT NULL,
    role ENUM('student','admin') DEFAULT 'student',
    INDEX(email)
) ENGINE=InnoDB;
''')

conn.commit()
curs.close()
conn.close()

print("✅ users table created (if it did not already exist)")
