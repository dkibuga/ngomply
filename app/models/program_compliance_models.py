from app import db
from datetime import datetime

class ProgramArea(db.Model):
    """Model for program/sector areas with specific compliance requirements"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    ministry = db.Column(db.String(100), nullable=True)  # Relevant government ministry
    sector_code = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requirements = db.relationship('SectorRequirement', backref='program_area', lazy='dynamic')
    
    def __repr__(self):
        return f'<ProgramArea {self.name}>'

class SectorRequirement(db.Model):
    """Model for sector-specific compliance requirements"""
    id = db.Column(db.Integer, primary_key=True)
    program_area_id = db.Column(db.Integer, db.ForeignKey('program_area.id'))
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    legal_reference = db.Column(db.String(200), nullable=True)
    authority = db.Column(db.String(100))  # Regulatory authority
    frequency = db.Column(db.String(50))  # annual, quarterly, monthly, one-time
    penalty = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SectorRequirement {self.title}>'

class OrganizationProgram(db.Model):
    """Association model between organizations and program areas"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    program_area_id = db.Column(db.Integer, db.ForeignKey('program_area.id'))
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='program_areas_assoc')
    program_area = db.relationship('ProgramArea', backref='organizations_assoc')
    
    def __repr__(self):
        return f'<OrganizationProgram {self.organization_id}:{self.program_area_id}>'

class LocalPermit(db.Model):
    """Model for local government permits and authorizations"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    permit_type = db.Column(db.String(100))
    permit_number = db.Column(db.String(50))
    issuing_authority = db.Column(db.String(100))
    issue_date = db.Column(db.DateTime)
    expiry_date = db.Column(db.DateTime, nullable=True)
    jurisdiction = db.Column(db.String(100))  # District, municipality, etc.
    status = db.Column(db.String(20), default='active')  # active, expired, revoked
    file_path = db.Column(db.String(200), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='local_permits')
    creator = db.relationship('User', backref='local_permits')
    
    def __repr__(self):
        return f'<LocalPermit {self.permit_number}>'

class ComplianceRisk(db.Model):
    """Model for compliance risk assessments"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    program_area_id = db.Column(db.Integer, db.ForeignKey('program_area.id'), nullable=True)
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    likelihood = db.Column(db.Integer)  # 1-5 scale
    impact = db.Column(db.Integer)  # 1-5 scale
    risk_level = db.Column(db.String(20))  # low, medium, high, critical
    mitigation_plan = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='identified')  # identified, mitigated, accepted
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='compliance_risks')
    program_area = db.relationship('ProgramArea', backref='compliance_risks')
    creator = db.relationship('User', backref='compliance_risks')
    
    def __repr__(self):
        return f'<ComplianceRisk {self.title}>'
