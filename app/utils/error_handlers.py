import logging
from flask import request, current_app, jsonify
from werkzeug.exceptions import HTTPException
import traceback

def init_error_handlers(app):
    """
    Initialize global error handlers for the application
    
    Args:
        app: Flask application instance
    """
    # Configure logging
    if not app.debug:
        file_handler = logging.FileHandler('app.log')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('NGOmply startup')

    # Handle 404 errors
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.info(f"404 error: {request.path}")
        return render_template('errors/404.html'), 404

    # Handle 403 errors
    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f"403 error: {request.path} - User: {current_user.id if hasattr(current_user, 'id') else 'Anonymous'}")
        return render_template('errors/403.html'), 403

    # Handle 401 errors
    @app.errorhandler(401)
    def unauthorized_error(error):
        app.logger.warning(f"401 error: {request.path}")
        return render_template('errors/401.html'), 401

    # Handle 400 errors
    @app.errorhandler(400)
    def bad_request_error(error):
        app.logger.warning(f"400 error: {request.path} - {error}")
        return render_template('errors/400.html'), 400

    # Handle 429 errors (too many requests)
    @app.errorhandler(429)
    def too_many_requests_error(error):
        app.logger.warning(f"429 error: {request.path} - {request.remote_addr}")
        return render_template('errors/429.html'), 429

    # Handle 500 errors
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 error: {request.path} - {error}\n{traceback.format_exc()}")
        return render_template('errors/500.html'), 500

    # Handle all HTTP exceptions
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        app.logger.warning(f"HTTP error {error.code}: {request.path} - {error}")
        return render_template(f'errors/{error.code}.html'), error.code

    # Handle all other exceptions
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {request.path} - {error}\n{traceback.format_exc()}")
        return render_template('errors/500.html'), 500

    # API error handler
    @app.errorhandler(Exception)
    def handle_api_exception(error):
        """Handle exceptions for API routes"""
        if request.path.startswith('/api/'):
            code = 500
            if isinstance(error, HTTPException):
                code = error.code
            
            response = {
                'success': False,
                'error': {
                    'code': code,
                    'message': str(error)
                }
            }
            
            app.logger.error(f"API error: {request.path} - {error}")
            return jsonify(response), code

def standardize_api_response(data=None, message=None, success=True, status_code=200):
    """
    Standardize API response format
    
    Args:
        data: Response data
        message: Response message
        success: Whether the request was successful
        status_code: HTTP status code
        
    Returns:
        tuple: (response_json, status_code)
    """
    response = {
        'success': success,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
        
    return jsonify(response), status_code

# Import at the end to avoid circular imports
from flask import render_template
from flask_login import current_user

from flask import render_template, jsonify, request

def register_error_handlers(app):
    """Register error handlers with the Flask application."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        if request.is_json:
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        if request.is_json:
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(400)
    def bad_request_error(error):
        if request.is_json:
            return jsonify({'error': 'Bad request'}), 400
        return render_template('errors/400.html'), 400
