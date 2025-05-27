from app import db
from datetime import datetime
import json

class ComplianceMetric(db.Model):
    """Model for compliance metrics and KPIs"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    metric_type = db.Column(db.String(50))  # task_completion, document_validity, risk_level
    target_value = db.Column(db.Float, nullable=True)
    current_value = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(20), nullable=True)  # percentage, days, count
    status = db.Column(db.String(20))  # on_track, at_risk, critical
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='compliance_metrics')
    
    def __repr__(self):
        return f'<ComplianceMetric {self.name}>'

class ComplianceSnapshot(db.Model):
    """Model for point-in-time compliance status snapshots"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    snapshot_date = db.Column(db.DateTime, default=datetime.utcnow)
    compliance_score = db.Column(db.Float)  # 0-100 scale
    tasks_total = db.Column(db.Integer)
    tasks_completed = db.Column(db.Integer)
    documents_total = db.Column(db.Integer)
    documents_valid = db.Column(db.Integer)
    risks_total = db.Column(db.Integer)
    risks_mitigated = db.Column(db.Integer)
    metrics_data = db.Column(db.Text)  # JSON string of metrics
    
    # Relationships
    organization = db.relationship('Organization', backref='compliance_snapshots')
    
    def __repr__(self):
        return f'<ComplianceSnapshot {self.snapshot_date}>'
    
    def set_metrics_data(self, metrics_dict):
        """Store metrics as JSON string"""
        self.metrics_data = json.dumps(metrics_dict)
    
    def get_metrics_data(self):
        """Retrieve metrics as dictionary"""
        if self.metrics_data:
            return json.loads(self.metrics_data)
        return {}

class ComplianceAlert(db.Model):
    """Model for compliance alerts and notifications"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    title = db.Column(db.String(120))
    message = db.Column(db.Text)
    alert_type = db.Column(db.String(50))  # deadline, expiry, risk, score_change
    severity = db.Column(db.String(20))  # info, warning, critical
    related_entity_type = db.Column(db.String(50), nullable=True)  # task, document, permit
    related_entity_id = db.Column(db.Integer, nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='compliance_alerts')
    
    def __repr__(self):
        return f'<ComplianceAlert {self.title}>'

class ComplianceBenchmark(db.Model):
    """Model for industry benchmarks and comparisons"""
    id = db.Column(db.Integer, primary_key=True)
    sector = db.Column(db.String(100))  # Health, Education, etc.
    organization_size = db.Column(db.String(20))  # small, medium, large
    metric_name = db.Column(db.String(100))
    average_value = db.Column(db.Float)
    median_value = db.Column(db.Float, nullable=True)
    top_quartile_value = db.Column(db.Float, nullable=True)
    sample_size = db.Column(db.Integer)
    effective_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ComplianceBenchmark {self.metric_name}>'

class ComplianceReport(db.Model):
    """Model for generated compliance reports"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    title = db.Column(db.String(120))
    report_type = db.Column(db.String(50))  # summary, detailed, trend, benchmark
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    file_path = db.Column(db.String(200), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='compliance_reports')
    creator = db.relationship('User', backref='compliance_reports')
    
    def __repr__(self):
        return f'<ComplianceReport {self.title}>'
