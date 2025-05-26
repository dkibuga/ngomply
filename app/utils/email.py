from flask_mail import Mail, Message
from threading import Thread
from flask import current_app, render_template

mail = Mail()

def send_async_email(app, msg):
    """
    Send email asynchronously
    
    Args:
        app: Flask application context
        msg: Email message to send
    """
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body=None, sender=None, attachments=None):
    """
    Send an email
    
    Args:
        subject (str): Email subject
        recipients (list): List of recipient email addresses
        text_body (str): Plain text email body
        html_body (str, optional): HTML email body. Defaults to None.
        sender (str, optional): Email sender. Defaults to None (uses default sender).
        attachments (list, optional): List of attachments. Defaults to None.
            Each attachment should be a tuple (filename, content_type, data)
    """
    if sender is None:
        sender = current_app.config['MAIL_DEFAULT_SENDER']
        
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    
    if html_body:
        msg.html = html_body
        
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)
    
    # Send email asynchronously
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def send_password_reset_email(user):
    """
    Send password reset email to user
    
    Args:
        user: User object
    """
    token = user.get_reset_password_token()
    send_email(
        subject='[NGOmply] Reset Your Password',
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt', user=user, token=token),
        html_body=render_template('email/reset_password.html', user=user, token=token)
    )

def send_email_verification(user):
    """
    Send email verification to user
    
    Args:
        user: User object
    """
    token = user.get_email_verification_token()
    send_email(
        subject='[NGOmply] Verify Your Email',
        recipients=[user.email],
        text_body=render_template('email/verify_email.txt', user=user, token=token),
        html_body=render_template('email/verify_email.html', user=user, token=token)
    )

def send_notification_email(user, subject, message):
    """
    Send notification email to user
    
    Args:
        user: User object
        subject (str): Email subject
        message (str): Email message
    """
    send_email(
        subject=f'[NGOmply] {subject}',
        recipients=[user.email],
        text_body=message,
        html_body=f'<p>{message}</p>'
    )
