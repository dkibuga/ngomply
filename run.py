from flask import Flask, render_template
from app import create_app, db
from app.models.models import User, Organization, Document, ComplianceTask, LegalDocument, Form, AuditLog
from app.utils.login import load_user

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Organization': Organization,
        'Document': Document,
        'ComplianceTask': ComplianceTask,
        'LegalDocument': LegalDocument,
        'Form': Form,
        'AuditLog': AuditLog
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
