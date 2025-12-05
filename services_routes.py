from flask import Blueprint, render_template

services_bp = Blueprint('services', __name__, url_prefix='/services')

@services_bp.route('/')
def list_services():
    return render_template('services/list.html', services=[])