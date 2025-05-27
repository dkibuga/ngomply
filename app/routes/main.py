from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.models import ComplianceTask  # Added import
from datetime import datetime  # Added import

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    if current_user.is_authenticated:
        now = datetime.utcnow()  # Added datetime object
        return render_template('main/index.html', title='Dashboard', ComplianceTask=ComplianceTask, now=now)  # Added context variables
    return render_template('main/landing.html', title='Welcome to NGOmply')

