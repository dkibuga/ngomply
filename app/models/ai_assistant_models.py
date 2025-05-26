from app import db
from datetime import datetime
import json

class AIComplianceQuery(db.Model):
    """Model for tracking AI compliance assistant queries"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    query_text = db.Column(db.Text)
    response_text = db.Column(db.Text)
    context_data = db.Column(db.Text, nullable=True)  # JSON string of context
    query_category = db.Column(db.String(50), nullable=True)  # auto-categorized topic
    feedback_rating = db.Column(db.Integer, nullable=True)  # 1-5 rating
    feedback_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='ai_queries')
    user = db.relationship('User', backref='ai_queries')
    
    def __repr__(self):
        return f'<AIComplianceQuery {self.id}>'
    
    def set_context_data(self, context_dict):
        """Store context as JSON string"""
        self.context_data = json.dumps(context_dict)
    
    def get_context_data(self):
        """Retrieve context as dictionary"""
        if self.context_data:
            return json.loads(self.context_data)
        return {}

class AIComplianceTemplate(db.Model):
    """Model for AI-generated compliance document templates"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    document_type = db.Column(db.String(50))  # policy, procedure, report, checklist
    content = db.Column(db.Text)
    variables = db.Column(db.Text)  # JSON string of variable placeholders
    is_public = db.Column(db.Boolean, default=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='ai_templates')
    creator = db.relationship('User', backref='ai_templates')
    
    def __repr__(self):
        return f'<AIComplianceTemplate {self.title}>'
    
    def set_variables(self, variables_dict):
        """Store variables as JSON string"""
        self.variables = json.dumps(variables_dict)
    
    def get_variables(self):
        """Retrieve variables as dictionary"""
        if self.variables:
            return json.loads(self.variables)
        return {}

class RegulatoryUpdate(db.Model):
    """Model for tracking regulatory updates and changes"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    source = db.Column(db.String(100))
    publication_date = db.Column(db.DateTime)
    effective_date = db.Column(db.DateTime, nullable=True)
    regulatory_body = db.Column(db.String(100))
    impact_level = db.Column(db.String(20))  # low, medium, high
    sectors_affected = db.Column(db.Text)  # JSON string of affected sectors
    url = db.Column(db.String(200), nullable=True)
    file_path = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<RegulatoryUpdate {self.title}>'
    
    def set_sectors_affected(self, sectors_list):
        """Store sectors as JSON string"""
        self.sectors_affected = json.dumps(sectors_list)
    
    def get_sectors_affected(self):
        """Retrieve sectors as list"""
        if self.sectors_affected:
            return json.loads(self.sectors_affected)
        return []

class AIAnalysisResult(db.Model):
    """Model for AI document analysis results"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    analysis_type = db.Column(db.String(50))  # compliance_gap, risk_assessment, improvement
    summary = db.Column(db.Text)
    findings = db.Column(db.Text)  # JSON string of findings
    recommendations = db.Column(db.Text)
    confidence_score = db.Column(db.Float)  # 0-1 scale
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='ai_analyses')
    document = db.relationship('Document', backref='ai_analyses')
    
    def __repr__(self):
        return f'<AIAnalysisResult {self.id}>'
    
    def set_findings(self, findings_list):
        """Store findings as JSON string"""
        self.findings = json.dumps(findings_list)
    
    def get_findings(self):
        """Retrieve findings as list"""
        if self.findings:
            return json.loads(self.findings)
        return []
