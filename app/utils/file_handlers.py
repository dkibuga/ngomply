from flask import current_app, request, abort
import os
import magic
import uuid
import re
from werkzeug.utils import secure_filename

# Allowed file extensions and MIME types
ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'txt': 'text/plain',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png'
}

def allowed_file(filename):
    """
    Check if a file is allowed based on its extension
    
    Args:
        filename (str): Name of the file to check
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_type(file_path):
    """
    Validate file type using MIME type detection
    
    Args:
        file_path (str): Path to the file to validate
        
    Returns:
        bool: True if file MIME type is allowed, False otherwise
    """
    try:
        mime = magic.Magic(mime=True)
        file_mime = mime.from_file(file_path)
        
        # Check if the detected MIME type is in our allowed list
        return file_mime in ALLOWED_EXTENSIONS.values()
    except Exception as e:
        current_app.logger.error(f"Error validating file type: {str(e)}")
        return False

def create_organization_upload_folder(organization_id):
    """
    Create upload folder for an organization
    
    Args:
        organization_id (int): ID of the organization
        
    Returns:
        str: Path to the organization's upload folder
    """
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], f'org_{organization_id}')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder

def save_file(file, folder):
    """
    Save a file securely
    
    Args:
        file: File object to save
        folder (str): Folder to save the file in
        
    Returns:
        str: Path to the saved file
    """
    # Secure the filename to prevent directory traversal attacks
    filename = secure_filename(file.filename)
    
    # Generate a unique filename to prevent overwriting
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    # Create the full file path
    file_path = os.path.join(folder, unique_filename)
    
    # Save the file
    file.save(file_path)
    
    # Validate the file type after saving
    if not validate_file_type(file_path):
        # If file type is not allowed, delete the file and abort
        os.remove(file_path)
        current_app.logger.warning(f"Invalid file type detected and removed: {file_path}")
        abort(400, "Invalid file type detected")
    
    return file_path

def sanitize_filename(filename):
    """
    Sanitize a filename to remove potentially dangerous characters
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Replace potentially dangerous characters
    filename = re.sub(r'[^\w\.-]', '_', filename)
    
    return filename

def get_file_path(organization_id, filename):
    """
    Get the full path to a file for an organization
    
    Args:
        organization_id (int): ID of the organization
        filename (str): Name of the file
        
    Returns:
        str: Full path to the file
    """
    # Sanitize the filename
    filename = sanitize_filename(filename)
    
    # Get the organization's upload folder
    folder = create_organization_upload_folder(organization_id)
    
    # Return the full path
    return os.path.join(folder, filename)

def delete_file(file_path):
    """
    Delete a file securely
    
    Args:
        file_path (str): Path to the file to delete
        
    Returns:
        bool: True if file was deleted successfully, False otherwise
    """
    try:
        # Check if file exists
        if os.path.exists(file_path):
            # Delete the file
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        current_app.logger.error(f"Error deleting file: {str(e)}")
        return False
