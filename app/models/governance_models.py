from app import db
from datetime import datetime

class BoardMeeting(db.Model):
    """Model for board meetings and minutes"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    title = db.Column(db.String(120))
    meeting_date = db.Column(db.DateTime)
    location = db.Column(db.String(200))
    attendees = db.Column(db.Text)
    agenda = db.Column(db.Text)
    minutes = db.Column(db.Text, nullable=True)
    resolutions = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    minutes_approved = db.Column(db.Boolean, default=False)
    minutes_approval_date = db.Column(db.DateTime, nullable=True)
    file_path = db.Column(db.String(200), nullable=True)  # For uploaded minutes document
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='board_meetings')
    creator = db.relationship('User', backref='board_meetings')
    
    def __repr__(self):
        return f'<BoardMeeting {self.title}>'

class BoardMember(db.Model):
    """Model for board members"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    name = db.Column(db.String(100))
    position = db.Column(db.String(100))  # e.g., Chairperson, Secretary, Treasurer
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='board_members')
    conflict_declarations = db.relationship('ConflictOfInterest', backref='board_member', lazy='dynamic')
    
    def __repr__(self):
        return f'<BoardMember {self.name}>'

class ConflictOfInterest(db.Model):
    """Model for conflict of interest declarations"""
    id = db.Column(db.Integer, primary_key=True)
    board_member_id = db.Column(db.Integer, db.ForeignKey('board_member.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    description = db.Column(db.Text)
    nature = db.Column(db.String(100))  # financial, relationship, other
    declaration_date = db.Column(db.DateTime)
    resolution = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='declared')  # declared, managed, resolved
    file_path = db.Column(db.String(200), nullable=True)  # For uploaded declaration document
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='conflict_declarations')
    
    def __repr__(self):
        return f'<ConflictOfInterest {self.id}>'

class GovernancePolicy(db.Model):
    """Model for governance policies"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    title = db.Column(db.String(120))
    policy_type = db.Column(db.String(50))  # board_charter, conflict_of_interest, whistleblower
    content = db.Column(db.Text)
    version = db.Column(db.String(20))
    approval_date = db.Column(db.DateTime)
    review_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='draft')  # draft, approved, archived
    approved_by = db.Column(db.String(100), nullable=True)
    file_path = db.Column(db.String(200), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='governance_policies')
    creator = db.relationship('User', backref='governance_policies')
    
    def __repr__(self):
        return f'<GovernancePolicy {self.title}>'

class BoardEvaluation(db.Model):
    """Model for board performance evaluations"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    title = db.Column(db.String(120))
    evaluation_date = db.Column(db.DateTime)
    evaluation_period = db.Column(db.String(50))  # e.g., "2024-2025"
    methodology = db.Column(db.Text)
    strengths = db.Column(db.Text, nullable=True)
    weaknesses = db.Column(db.Text, nullable=True)
    recommendations = db.Column(db.Text, nullable=True)
    action_plan = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed
    file_path = db.Column(db.String(200), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='board_evaluations')
    creator = db.relationship('User', backref='board_evaluations')
    
    def __repr__(self):
        return f'<BoardEvaluation {self.title}>'
