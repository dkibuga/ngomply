from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import jwt
from time import time
from flask import current_app

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    email_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='user')  # 'user', 'staff', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=3600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    def get_email_verification_token(self, expires_in=86400):
        return jwt.encode(
            {'verify_email': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
            return User.query.get(id)
        except:
            return None
    
    @staticmethod
    def verify_email_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['verify_email']
            return User.query.get(id)
        except:
            return None

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), index=True)
    org_type = db.Column(db.String(20))  # NGO or CBO
    ngo_type = db.Column(db.String(50), nullable=True)  # Indigenous, Regional, Continental, Foreign, International
    registration_date = db.Column(db.DateTime, nullable=True)
    registration_number = db.Column(db.String(50), nullable=True)
    permit_expiry_date = db.Column(db.DateTime, nullable=True)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='organization', lazy='dynamic')
    documents = db.relationship('Document', backref='organization', lazy='dynamic', cascade='all, delete-orphan')
    compliance_tasks = db.relationship('ComplianceTask', backref='organization', lazy='dynamic', cascade='all, delete-orphan')
    
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    document_type = db.Column(db.String(50))  # Certificate, Form, Template, etc.
    file_path = db.Column(db.String(200))
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    file_extension = db.Column(db.String(10), nullable=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    user = db.relationship('User', backref='uploaded_documents')
    
class ComplianceTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime, nullable=True)
    task_type = db.Column(db.String(50))  # Annual Return, Audit, Permit Renewal, etc.
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    completed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_tasks')
    completer = db.relationship('User', foreign_keys=[completed_by], backref='completed_tasks')
    
class LegalDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    document_type = db.Column(db.String(50))  # Act, Regulation, Guideline, etc.
    content = db.Column(db.Text)
    file_path = db.Column(db.String(200), nullable=True)
    publication_date = db.Column(db.DateTime, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    form_code = db.Column(db.String(20))  # Form A, Form D, Form H, etc.
    description = db.Column(db.Text)
    file_path = db.Column(db.String(200))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(50))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(120))
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='notifications')

class AIGeneratedDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    content = db.Column(db.Text)
    document_type = db.Column(db.String(50))  # Constitution, Minutes, Letter, Audit Methodology
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    organization = db.relationship('Organization', backref='ai_documents')
    user = db.relationship('User', backref='ai_documents')
