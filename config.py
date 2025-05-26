import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.googlemail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@ngomply.com'
    
    # AI configuration - Using Anthropic Claude
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    
    # Security configuration
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE') == 'True'
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE') == 'True'
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Application configuration
    APP_NAME = 'NGOmply'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@ngomply.com'
