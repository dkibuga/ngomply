from app import db
from datetime import datetime

class DataProtectionAssessment(db.Model):
    """Model for data protection impact assessments"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    processing_purpose = db.Column(db.Text)
    data_categories = db.Column(db.Text)
    data_subjects = db.Column(db.Text)
    risk_assessment = db.Column(db.Text)
    mitigation_measures = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')  # draft, completed, reviewed
    completed_date = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='data_protection_assessments')
    creator = db.relationship('User', backref='data_protection_assessments')
    
    def __repr__(self):
        return f'<DataProtectionAssessment {self.id}>'

class ConsentRecord(db.Model):
    """Model for tracking data subject consent"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    subject_name = db.Column(db.String(100))
    subject_identifier = db.Column(db.String(100))  # email, ID number, etc.
    purpose = db.Column(db.Text)
    consent_given = db.Column(db.Boolean, default=False)
    consent_date = db.Column(db.DateTime, nullable=True)
    expiry_date = db.Column(db.DateTime, nullable=True)
    withdrawal_date = db.Column(db.DateTime, nullable=True)
    consent_proof = db.Column(db.String(200), nullable=True)  # file path or reference
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='consent_records')
    creator = db.relationship('User', backref='consent_records')
    
    def __repr__(self):
        return f'<ConsentRecord {self.subject_identifier}>'

class DataBreachRecord(db.Model):
    """Model for data breach notifications and tracking"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    breach_date = db.Column(db.DateTime)
    discovery_date = db.Column(db.DateTime)
    description = db.Column(db.Text)
    data_affected = db.Column(db.Text)
    subjects_affected = db.Column(db.Integer)
    risk_assessment = db.Column(db.Text)
    mitigation_steps = db.Column(db.Text)
    reported_to_authority = db.Column(db.Boolean, default=False)
    authority_report_date = db.Column(db.DateTime, nullable=True)
    subjects_notified = db.Column(db.Boolean, default=False)
    subject_notification_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='open')  # open, mitigated, closed
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='data_breaches')
    creator = db.relationship('User', backref='data_breaches')
    
    def __repr__(self):
        return f'<DataBreachRecord {self.id}>'

class PDPORegistration(db.Model):
    """Model for tracking PDPO registration status"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), unique=True)
    registration_number = db.Column(db.String(50), nullable=True)
    registration_date = db.Column(db.DateTime, nullable=True)
    renewal_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='not_registered')  # not_registered, pending, registered, expired
    annual_report_submitted = db.Column(db.Boolean, default=False)
    last_report_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='pdpo_registration')
    
    def __repr__(self):
        return f'<PDPORegistration {self.organization_id}>'

class DataProtectionPolicy(db.Model):
    """Model for data protection policies"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    title = db.Column(db.String(120))
    content = db.Column(db.Text)
    version = db.Column(db.String(20))
    effective_date = db.Column(db.DateTime)
    review_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='draft')  # draft, active, archived
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='data_protection_policies')
    creator = db.relationship('User', backref='data_protection_policies')
    
    def __repr__(self):
        return f'<DataProtectionPolicy {self.id}>'
