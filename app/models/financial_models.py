from app import db
from datetime import datetime

class FinancialReport(db.Model):
    """Model for financial reports and statements"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    title = db.Column(db.String(120))
    report_type = db.Column(db.String(50))  # annual_return, audit, financial_statement, budget
    fiscal_year = db.Column(db.String(9))  # e.g., "2024-2025"
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    file_path = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='draft')  # draft, final, submitted
    submission_date = db.Column(db.DateTime, nullable=True)
    submitted_to = db.Column(db.String(100), nullable=True)  # e.g., "NGO Bureau", "Tax Authority"
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='financial_reports')
    creator = db.relationship('User', backref='financial_reports')
    
    def __repr__(self):
        return f'<FinancialReport {self.title}>'

class BudgetItem(db.Model):
    """Model for budget line items"""
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('financial_report.id'))
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    amount_budgeted = db.Column(db.Float)
    amount_actual = db.Column(db.Float, nullable=True)
    variance = db.Column(db.Float, nullable=True)
    variance_explanation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    report = db.relationship('FinancialReport', backref='budget_items')
    
    def __repr__(self):
        return f'<BudgetItem {self.category}>'

class TaxExemption(db.Model):
    """Model for tax exemption certificates and status"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    certificate_number = db.Column(db.String(50))
    issue_date = db.Column(db.DateTime)
    expiry_date = db.Column(db.DateTime, nullable=True)
    tax_type = db.Column(db.String(50))  # income_tax, vat, import_duty
    issuing_authority = db.Column(db.String(100))
    file_path = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='active')  # active, expired, revoked
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='tax_exemptions')
    creator = db.relationship('User', backref='tax_exemptions')
    
    def __repr__(self):
        return f'<TaxExemption {self.certificate_number}>'

class AuditFinding(db.Model):
    """Model for tracking audit findings and resolutions"""
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('financial_report.id'))
    finding_type = db.Column(db.String(50))  # material_weakness, significant_deficiency, compliance
    description = db.Column(db.Text)
    recommendation = db.Column(db.Text)
    management_response = db.Column(db.Text, nullable=True)
    action_plan = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved
    resolution_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    report = db.relationship('FinancialReport', backref='audit_findings')
    
    def __repr__(self):
        return f'<AuditFinding {self.id}>'

class FinancialPolicy(db.Model):
    """Model for financial policies and procedures"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    title = db.Column(db.String(120))
    policy_type = db.Column(db.String(50))  # procurement, travel, asset_management
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
    organization = db.relationship('Organization', backref='financial_policies')
    creator = db.relationship('User', backref='financial_policies')
    
    def __repr__(self):
        return f'<FinancialPolicy {self.title}>'
