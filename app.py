"""
Campus Connect - Main Application Module

This is the Flask application entry point that:
  - Initializes the Flask app with security configuration
  - Registers all feature blueprints (resources, events, services, comments, votes, auth)
  - Defines top-level routes (home page, about page)
  - Manages the application lifecycle

Blueprints registered here handle their respective domains:
  - auth_bp (login.py): User authentication and registration
  - resource_bp: Community resources listing and management
  - event_bp: Campus events listing and management
  - services_bp: Student services listing and management
  - comment_routes: Comments on resources and events
  - votes_bp: Upvoting/downvoting system
"""

from flask import (Flask, render_template, url_for, request,
                   redirect, flash, session,)
import secrets
import cs304dbi as dbi
from resources_routes import resource_bp
from event_routes import event_bp
from comment_routes import comment_routes
from vote_routes import votes_bp
from services_routes import services_bp


app = Flask(__name__)
app.secret_key = secrets.token_hex()
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

from login import auth_bp
app.register_blueprint(auth_bp)
app.register_blueprint(resource_bp)
app.register_blueprint(event_bp)
app.register_blueprint(comment_routes)
app.register_blueprint(votes_bp)
app.register_blueprint(services_bp)

@app.route('/')
def index():
    return render_template('login.html', page_title='Main Page')

@app.route('/about/')
def about():
    return render_template('about.html', page_title='About Us')

if __name__ == '__main__':
    import sys, os
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        assert(port > 1024)
    else:
        port = os.getuid()
    app.debug = True
    app.run('0.0.0.0', port)
