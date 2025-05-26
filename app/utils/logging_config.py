import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    """
    Set up comprehensive logging for the application
    
    Args:
        app: Flask application instance
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Configure main application logger
    file_handler = RotatingFileHandler('logs/ngomply.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    
    # Set up separate loggers for different components
    loggers = {
        'auth': setup_component_logger('auth'),
        'file': setup_component_logger('file'),
        'ai': setup_component_logger('ai'),
        'security': setup_component_logger('security'),
        'db': setup_component_logger('db')
    }
    
    app.logger.info('NGOmply logging initialized')
    return loggers

def setup_component_logger(component_name):
    """
    Set up logger for a specific component
    
    Args:
        component_name: Name of the component
        
    Returns:
        Logger: Configured logger for the component
    """
    logger = logging.getLogger(f'ngomply.{component_name}')
    handler = RotatingFileHandler(f'logs/{component_name}.log', maxBytes=10240, backupCount=5)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def log_user_activity(logger, user_id, activity, details=None):
    """
    Log user activity for audit purposes
    
    Args:
        logger: Logger to use
        user_id: ID of the user performing the activity
        activity: Description of the activity
        details: Additional details about the activity
    """
    log_message = f"User {user_id}: {activity}"
    if details:
        log_message += f" - {details}"
    logger.info(log_message)

def log_security_event(logger, event_type, details, user_id=None, severity='INFO'):
    """
    Log security-related events
    
    Args:
        logger: Logger to use
        event_type: Type of security event
        details: Details about the event
        user_id: ID of the user related to the event (if applicable)
        severity: Severity level of the event
    """
    log_message = f"SECURITY {event_type}"
    if user_id:
        log_message += f" - User {user_id}"
    log_message += f": {details}"
    
    if severity == 'INFO':
        logger.info(log_message)
    elif severity == 'WARNING':
        logger.warning(log_message)
    elif severity == 'ERROR':
        logger.error(log_message)
    elif severity == 'CRITICAL':
        logger.critical(log_message)
