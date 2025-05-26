import os
from flask import current_app
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

def allowed_file(filename, allowed_extensions=None):
    """
    Check if the file has an allowed extension
    
    Args:
        filename (str): The filename to check
        allowed_extensions (list, optional): List of allowed extensions. Defaults to None.
    
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    if allowed_extensions is None:
        allowed_extensions = ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png']
        
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, directory=None):
    """
    Save a file to the specified directory with a secure filename
    
    Args:
        file: The file object to save
        directory (str, optional): Directory to save the file. Defaults to uploads directory.
    
    Returns:
        str: The path where the file was saved
    """
    if directory is None:
        directory = os.path.join(current_app.config['UPLOAD_FOLDER'])
    
    # Create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Generate a secure filename with UUID to prevent duplicates
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    # Save the file
    file_path = os.path.join(directory, unique_filename)
    file.save(file_path)
    
    return file_path

def get_file_extension(filename):
    """
    Get the extension of a file
    
    Args:
        filename (str): The filename
    
    Returns:
        str: The file extension
    """
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def create_organization_upload_folder(org_id):
    """
    Create a folder for an organization's uploads
    
    Args:
        org_id (int): The organization ID
    
    Returns:
        str: The path to the organization's upload folder
    """
    org_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], f'org_{org_id}')
    if not os.path.exists(org_folder):
        os.makedirs(org_folder)
    return org_folder
