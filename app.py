from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
import secrets
import cs304dbi as dbi
from resources_routes import resource_bp


app = Flask(__name__)
app.secret_key = secrets.token_hex()
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

print(dbi.conf('cs304jas_db'))

from resources_routes import resource_bp
app.register_blueprint(resource_bp)

@app.route('/')
def index():
    return render_template('main.html', page_title='Main Page')

@app.route('/about/')
def about():
    flash('this is a flashed message')
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
