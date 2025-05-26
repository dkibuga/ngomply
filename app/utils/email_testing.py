from flask import render_template, current_app
from app.utils.email import send_email

def test_email_templates():
    """
    Function to test email templates in development environment
    
    This function renders all email templates with test data and can be used
    to verify template rendering without actually sending emails.
    
    Returns:
        dict: Dictionary containing rendered templates
    """
    # Create test user data
    test_user = {
        'username': 'testuser',
        'email': 'test@example.com'
    }
    
    # Create test token
    test_token = 'test-token-12345'
    
    # Test templates
    templates = {
        'verify_email.txt': render_template('email/verify_email.txt', user=test_user, token=test_token),
        'verify_email.html': render_template('email/verify_email.html', user=test_user, token=test_token),
        'reset_password.txt': render_template('email/reset_password.txt', user=test_user, token=test_token),
        'reset_password.html': render_template('email/reset_password.html', user=test_user, token=test_token),
        'notification.txt': render_template('email/notification.txt', message='This is a test notification'),
        'notification.html': render_template('email/notification.html', message='This is a test notification')
    }
    
    return templates

def send_test_email(recipient):
    """
    Send a test email to verify email configuration
    
    Args:
        recipient (str): Email address to send test to
        
    Returns:
        bool: True if email was sent successfully
    """
    try:
        send_email(
            subject='[NGOmply] Test Email',
            recipients=[recipient],
            text_body='This is a test email from NGOmply.',
            html_body='<p>This is a test email from NGOmply.</p>'
        )
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending test email: {str(e)}")
        return False
