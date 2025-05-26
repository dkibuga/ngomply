from app import db
from datetime import datetime
import uuid

class ValueAddedService(db.Model):
    """Model for value-added services"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    service_type = db.Column(db.String(50))  # consultancy, training, audit_prep, review
    price = db.Column(db.Float)
    duration_hours = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('ServiceBooking', backref='service', lazy='dynamic')
    
    def __repr__(self):
        return f'<ValueAddedService {self.name}>'

class ServiceBooking(db.Model):
    """Model for value-added service bookings"""
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('value_added_service.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    booking_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    notes = db.Column(db.Text, nullable=True)
    payment_status = db.Column(db.String(20), default='unpaid')  # unpaid, paid, refunded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='service_bookings')
    user = db.relationship('User', backref='service_bookings')
    
    def __repr__(self):
        return f'<ServiceBooking {self.id}>'

class TrainingSession(db.Model):
    """Model for training sessions"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    training_type = db.Column(db.String(50))  # webinar, workshop, course
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    capacity = db.Column(db.Integer)
    current_participants = db.Column(db.Integer, default=0)
    location = db.Column(db.String(200), nullable=True)  # Physical or virtual
    is_public = db.Column(db.Boolean, default=True)
    price = db.Column(db.Float, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='training_sessions')
    registrations = db.relationship('TrainingRegistration', backref='session', lazy='dynamic')
    
    def __repr__(self):
        return f'<TrainingSession {self.title}>'

class TrainingRegistration(db.Model):
    """Model for training session registrations"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('training_session.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    attendance_status = db.Column(db.String(20), default='registered')  # registered, attended, no_show
    payment_status = db.Column(db.String(20), default='unpaid')  # unpaid, paid, refunded
    
    # Relationships
    organization = db.relationship('Organization', backref='training_registrations')
    user = db.relationship('User', backref='training_registrations')
    
    def __repr__(self):
        return f'<TrainingRegistration {self.id}>'

class ConsultancyProject(db.Model):
    """Model for consultancy projects"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    project_type = db.Column(db.String(50))  # compliance_audit, system_setup, policy_development
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed, cancelled
    deliverables = db.Column(db.Text, nullable=True)
    consultant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='consultancy_projects')
    consultant = db.relationship('User', backref='consultancy_projects')
    
    def __repr__(self):
        return f'<ConsultancyProject {self.title}>'

class DocumentWatermark(db.Model):
    """Model for document watermarking"""
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    watermark_text = db.Column(db.String(200))
    watermark_id = db.Column(db.String(50), default=lambda: str(uuid.uuid4())[:8].upper())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    document = db.relationship('Document', backref='watermark')
    creator = db.relationship('User', backref='created_watermarks')
    
    def __repr__(self):
        return f'<DocumentWatermark {self.watermark_id}>'
