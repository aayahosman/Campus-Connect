CREATE TABLE users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(80) NOT NULL,
  email VARCHAR(120) UNIQUE,
  password CHAR(60),
  role ENUM('student', 'admin')
);

CREATE TABLE events (
  event_id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(140),
  date_of_event DATETIME,
  created_by INT,
  created_at DATETIME,
  description TEXT NOT NULL,
  address1 VARCHAR(120),
  address2 VARCHAR(120),
  city VARCHAR(60),
  state CHAR(2),
  postal_code VARCHAR(10),
  FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE resources (
  resource_id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(140),
  description TEXT NOT NULL,
  category VARCHAR(100),
  contact_info VARCHAR(120),
  status ENUM('active','inactive'),
  created_by INT,
  created_at DATETIME,
  address1 VARCHAR(120),
  address2 VARCHAR(120),
  city VARCHAR(60),
  state CHAR(2),
  postal_code VARCHAR(10),
  FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE comments (
  comment_id INT AUTO_INCREMENT PRIMARY KEY,
  content TEXT NOT NULL,
  event_id INT,
  resource_id INT,
  created_by INT,
  created_at DATETIME,
  FOREIGN KEY (event_id) REFERENCES events(event_id),
  FOREIGN KEY (resource_id) REFERENCES resources(resource_id),
  FOREIGN KEY (created_by) REFERENCES users(user_id)
);

CREATE TABLE rsvp (
  rsvp_id INT AUTO_INCREMENT PRIMARY KEY,
  status ENUM('yes','no','maybe'),
  event_id INT,
  created_by INT,
  created_at DATETIME,
  FOREIGN KEY (event_id) REFERENCES events(event_id),
  FOREIGN KEY (created_by) REFERENCES users(user_id)
);
