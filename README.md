# Campus Connect: Student Community Resource & Events Platform

### Wellesley College CS304  
**Authors:** Aayah Osman, Julie Zeng, Shelley Zheng  

---

## Project Summary

Campus Connect is a student-built Flask web application that centralizes campus resources, services, and events into a single, community-driven platform. Instead of searching across emails, flyers, and group chats, students can use Campus Connect to discover support resources, browse events, and engage with their community in one place.

One-sentence summary:  
Campus Connect lets students share community resources, offer services, and create, browse, and RSVP to campus events.

---

## Core Features

- User authentication (sign up, log in, log out)
- CRUD functionality for resources, events, and services
- RSVP system for events
- Interactive monthly calendar view
- Comments on resources and events
- Community verification via upvotes and downvotes
- Automatic moderation based on voting thresholds
- Search and filter by keyword and category
- Dark mode toggle
- Session-based edit and delete permissions

---

## Community Moderation & Verification

Campus Connect uses a student-driven verification system to keep information accurate and trustworthy.

- Upvotes increase credibility  
  Items with enough upvotes are marked Verified by the Community
- Downvotes flag inaccurate or outdated information  
  Items may be marked Needs Review  
  Items with excessive downvotes are automatically removed from the platform
- Removed items trigger a flash message explaining the removal

This system helps ensure that content stays relevant, safe, and community-maintained.

---

## How to Run the Application

source venv/bin/activate  
python app.py  

---

## Project Structure

Campus-Connect/
- app.py
- auth_utils.py
- event_routes.py
- resource_routes.py
- services_routes.py
- vote_routes.py
- comment_routes.py
- schema.sql
- templates/
  - base.html
  - about.html
  - greet.html
  - login.html
  - signup.html
  - calendar_view.html
  - events/
  - resources/
  - services/
- static/
  - style.css

---

## Using the Application

### Browsing Content

- Anyone can browse resources, services, and events without logging in
- Use keyword search or category filters
- Clear filters to reset results

### Creating an Account

- Go to Sign Up
- Enter your name, email, password, and role
- You will be redirected to the welcome page upon success

### Logging In

- Enter your email and password on the login page
- Invalid credentials prompt a retry

---

## Resources

- Browse community-submitted resources such as food assistance, academic support, and technology help
- Logged-in users may add resources
- Only creators may edit or delete their resources
- Resources support voting and comments

---

## Events

- Create and browse campus and civic engagement events
- RSVP as Yes or Maybe
- View event attendees
- Browse events in an interactive calendar view
- Only creators may edit or delete their events

---

## Services

- Browse student-offered services such as tutoring, crafts, or beauty services
- Listings include pricing, availability, and contact information
- Only creators may edit or delete their services
- Services support community voting

---

## Comments

- Resources and events support comments
- Logged-in users may add, edit, or delete their own comments
- Comment updates happen dynamically without full page reloads

---

## Dark Mode

- Toggle light or dark mode using the icon in the navigation bar
- Theme preference persists across pages

---
### Virtual Environment Setup (CS304)

We followed the standard CS304 virtual environment setup:

```bash
python3.9 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install flask pymysql bcrypt pillow
~cs304flask/pub/bin/install-cs304dbi
```

---
## Sample Test Account

Email: testing@email.com  
Password: 123  

---

## Security Measures

- SQL Injection Prevention: Parameterized queries only
- XSS Protection: Jinja2 auto-escaping
- Access Control:
  - Edit and delete restricted to content creators
  - Unauthenticated users have read-only access
- Session-based authentication enforced on protected routes

---

## Notes & Future Improvements

© 2025 Campus Connect  
Created by Aayah Osman, Julie Zeng, Shelley Zheng
