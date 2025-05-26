from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    if current_user.is_authenticated:
        return render_template('main/index.html', title='Dashboard')
    return render_template('main/landing.html', title='Welcome to NGOmply')
