from flask import render_template, jsonify

def register_error_handlers(app):
    """Register error handlers for the application"""
    
    @app.errorhandler(400)
    def bad_request_error(error):
        if request_wants_json():
            return jsonify({"error": "Bad Request", "message": str(error)}), 400
        return render_template('errors/400.html', error=error), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        if request_wants_json():
            return jsonify({"error": "Unauthorized", "message": "Authentication required"}), 401
        return render_template('errors/401.html', error=error), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        if request_wants_json():
            return jsonify({"error": "Forbidden", "message": "You don't have permission to access this resource"}), 403
        return render_template('errors/403.html', error=error), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        if request_wants_json():
            return jsonify({"error": "Not Found", "message": "The requested resource was not found"}), 404
        return render_template('errors/404.html', error=error), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Server Error: {str(error)}")
        if request_wants_json():
            return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500
        return render_template('errors/500.html', error=error), 500
    
    @app.errorhandler(429)
    def too_many_requests(error):
        if request_wants_json():
            return jsonify({"error": "Too Many Requests", "message": "Rate limit exceeded"}), 429
        return render_template('errors/429.html', error=error), 429

def request_wants_json():
    """Check if the request wants a JSON response"""
    from flask import request
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']
