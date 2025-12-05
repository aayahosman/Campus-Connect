-- USERS
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(80) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash CHAR(60) NOT NULL,
    role ENUM('student','admin') DEFAULT NULL
);

-- EVENTS
CREATE TABLE events (
    event_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(140),
    date_of_event DATETIME,
    category VARCHAR(80),
    created_by INT,
    created_at DATETIME,
    description TEXT NOT NULL,
    contact_info VARCHAR(255),
    address1 VARCHAR(120),
    address2 VARCHAR(120),
    city VARCHAR(60),
    state CHAR(2),
    postal_code VARCHAR(10),
    upvotes INT NOT NULL DEFAULT 0,
    downvotes INT NOT NULL DEFAULT 0,
    status ENUM('active','flagged','removed') DEFAULT 'active',
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- RESOURCES
CREATE TABLE resources (
    resource_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(140),
    description TEXT NOT NULL,
    category VARCHAR(100),
    contact_info VARCHAR(120),
    status ENUM('active','flagged','removed') DEFAULT 'active',
    created_by INT,
    created_at DATETIME,
    address1 VARCHAR(120),
    address2 VARCHAR(120),
    city VARCHAR(60),
    state CHAR(2),
    postal_code VARCHAR(10),
    upvotes INT NOT NULL DEFAULT 0,
    downvotes INT NOT NULL DEFAULT 0,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- COMMENTS
CREATE TABLE comments (
    comment_id INT PRIMARY KEY AUTO_INCREMENT,
    content TEXT NOT NULL,
    event_id INT,
    resource_id INT,
    created_by INT,
    created_at DATETIME,
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- RSVP
CREATE TABLE rsvp (
    rsvp_id INT PRIMARY KEY AUTO_INCREMENT,
    status ENUM('yes','no','maybe'),
    event_id INT,
    created_by INT,
    created_at DATETIME,
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- VOTES
CREATE TABLE votes (
    vote_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    item_type ENUM('event','resource') NOT NULL,
    item_id INT NOT NULL,
    vote ENUM('up','down') NOT NULL,
    UNIQUE (user_id, item_type, item_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- SERVICES
CREATE TABLE IF NOT EXISTS services (
    service_id INT PRIMARY KEY AUTO_INCREMENT,
    service_name VARCHAR(140) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100),

    price_range VARCHAR(50),
    service_location_type ENUM('on-campus','off-campus','mobile','dorm') DEFAULT 'on-campus',
    availability VARCHAR(120),
    contact_method VARCHAR(200),

    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by) REFERENCES users(user_id)
);