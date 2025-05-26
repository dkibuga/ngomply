from flask import current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

def init_limiter(app):
    """Initialize rate limiter for the application"""
    limiter.init_app(app)
    
    # Apply specific rate limits to sensitive routes
    
    # Authentication routes
    limiter.limit("10 per minute")(app.view_functions['auth.login'])
    limiter.limit("3 per minute")(app.view_functions['auth.reset_password_request'])
    
    # API routes if any
    for endpoint, view_func in app.view_functions.items():
        if endpoint.startswith('api.'):
            limiter.limit("30 per minute")(view_func)
    
    return limiter
