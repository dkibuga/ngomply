from flask import session, current_app
from datetime import datetime, timedelta
import secrets

def init_session_management(app):
    """
    Initialize enhanced session management for the application
    
    Args:
        app: Flask application instance
    """
    # Set session configuration
    app.config.setdefault('PERMANENT_SESSION_LIFETIME', timedelta(hours=1))
    app.config.setdefault('SESSION_COOKIE_SECURE', True)
    app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
    app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')
    
    @app.before_request
    def before_request():
        """Check and manage session before each request"""
        # Check if session needs rotation (every 15 minutes)
        if 'last_rotated' not in session:
            rotate_session()
        else:
            last_rotated = datetime.fromisoformat(session['last_rotated'])
            if datetime.utcnow() - last_rotated > timedelta(minutes=15):
                rotate_session()
        
        # Check for session timeout
        if 'last_active' in session:
            last_active = datetime.fromisoformat(session['last_active'])
            if datetime.utcnow() - last_active > app.config['PERMANENT_SESSION_LIFETIME']:
                # Session has timed out, clear it
                session.clear()
        
        # Update last active timestamp
        session['last_active'] = datetime.utcnow().isoformat()

def rotate_session():
    """Rotate session by regenerating session ID"""
    # Store important session data
    temp_data = {}
    for key in list(session.keys()):
        if key not in ['_fresh', '_id', '_user_id', 'csrf_token', 'last_rotated', 'last_active']:
            temp_data[key] = session[key]
    
    # Clear session
    session.clear()
    
    # Restore important data
    for key, value in temp_data.items():
        session[key] = value
    
    # Set new rotation timestamp
    session['last_rotated'] = datetime.utcnow().isoformat()
    
    # Generate new CSRF token if using Flask-WTF
    if 'csrf_token' in session:
        session['csrf_token'] = secrets.token_hex(16)
