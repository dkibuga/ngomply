from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, send_file, jsonify
from flask_login import login_required, current_user
from app.models.models import LegalDocument, Form, Organization
from app import db
from datetime import datetime
import os

knowledge_base_bp = Blueprint('knowledge_base', __name__)

@knowledge_base_bp.route('/')
@login_required
def index():
    """Knowledge base home page"""
    # Get recent legal documents
    recent_documents = LegalDocument.query.order_by(LegalDocument.last_updated.desc()).limit(5).all()
    
    # Get available forms
    forms = Form.query.order_by(Form.name).all()
    
    return render_template('knowledge_base/index.html', 
                          recent_documents=recent_documents,
                          forms=forms)

@knowledge_base_bp.route('/legal_documents')
@login_required
def legal_documents():
    """List all legal documents"""
    # Get filter parameters
    document_type = request.args.get('type', 'all')
    
    # Base query
    query = LegalDocument.query
    
    # Apply filters
    if document_type != 'all':
        query = query.filter_by(document_type=document_type)
    
    # Get all document types for filter dropdown
    document_types = db.session.query(LegalDocument.document_type).distinct().all()
    document_types = [d[0] for d in document_types]
    
    # Get documents
    documents = query.order_by(LegalDocument.title).all()
    
    return render_template('knowledge_base/legal_documents.html', 
                          documents=documents,
                          document_types=document_types,
                          selected_type=document_type)

@knowledge_base_bp.route('/document/<int:document_id>')
@login_required
def view_document(document_id):
    """View a legal document"""
    document = LegalDocument.query.get_or_404(document_id)
    
    return render_template('knowledge_base/view_document.html', document=document)

@knowledge_base_bp.route('/forms')
@login_required
def forms():
    """List all forms"""
    # Get all forms
    forms = Form.query.order_by(Form.form_code).all()
    
    return render_template('knowledge_base/forms.html', forms=forms)

@knowledge_base_bp.route('/form/<int:form_id>/download')
@login_required
def download_form(form_id):
    """Download a form"""
    form = Form.query.get_or_404(form_id)
    
    # Check if file exists
    if not os.path.exists(form.file_path):
        flash('Form file not found.', 'danger')
        return redirect(url_for('knowledge_base.forms'))
    
    # Return file for download
    return send_file(form.file_path, as_attachment=True)

@knowledge_base_bp.route('/search')
@login_required
def search():
    """Search the knowledge base"""
    query = request.args.get('query', '')
    
    if not query:
        return render_template('knowledge_base/search.html')
    
    # Search legal documents
    legal_documents = LegalDocument.query.filter(
        (LegalDocument.title.ilike(f'%{query}%')) | 
        (LegalDocument.content.ilike(f'%{query}%'))
    ).all()
    
    # Search forms
    forms = Form.query.filter(
        (Form.name.ilike(f'%{query}%')) | 
        (Form.form_code.ilike(f'%{query}%')) |
        (Form.description.ilike(f'%{query}%'))
    ).all()
    
    # Combine results
    results = []
    
    for doc in legal_documents:
        snippet = doc.content[:200] + '...' if len(doc.content) > 200 else doc.content
        results.append({
            'title': doc.title,
            'type': doc.document_type,
            'snippet': snippet,
            'last_updated': doc.last_updated,
            'url': url_for('knowledge_base.view_document', document_id=doc.id)
        })
    
    for form in forms:
        results.append({
            'title': form.name,
            'type': f'Form {form.form_code}',
            'snippet': form.description[:200] + '...' if len(form.description) > 200 else form.description,
            'last_updated': form.last_updated,
            'url': url_for('knowledge_base.download_form', form_id=form.id)
        })
    
    # Sort results by last updated date
    results.sort(key=lambda x: x['last_updated'], reverse=True)
    
    return render_template('knowledge_base/search_results.html', 
                          query=query,
                          results=results)

@knowledge_base_bp.route('/guides')
@login_required
def guides():
    """List all guides"""
    return render_template('knowledge_base/guides.html')

@knowledge_base_bp.route('/guides/ngo_registration')
@login_required
def ngo_registration_guide():
    """NGO registration guide"""
    return render_template('knowledge_base/guides/ngo_registration.html')

@knowledge_base_bp.route('/guides/cbo_registration')
@login_required
def cbo_registration_guide():
    """CBO registration guide"""
    return render_template('knowledge_base/guides/cbo_registration.html')

@knowledge_base_bp.route('/guides/compliance')
@login_required
def compliance_guide():
    """Compliance guide"""
    return render_template('knowledge_base/guides/compliance.html')

@knowledge_base_bp.route('/guides/renewal')
@login_required
def renewal_guide():
    """Permit renewal guide"""
    return render_template('knowledge_base/guides/renewal.html')

@knowledge_base_bp.route('/api/documents')
@login_required
def api_documents():
    """API endpoint for legal documents"""
    documents = LegalDocument.query.all()
    result = []
    
    for doc in documents:
        result.append({
            'id': doc.id,
            'title': doc.title,
            'document_type': doc.document_type,
            'publication_date': doc.publication_date.isoformat() if doc.publication_date else None,
            'last_updated': doc.last_updated.isoformat()
        })
    
    return jsonify(result)

@knowledge_base_bp.route('/api/forms')
@login_required
def api_forms():
    """API endpoint for forms"""
    forms = Form.query.all()
    result = []
    
    for form in forms:
        result.append({
            'id': form.id,
            'name': form.name,
            'form_code': form.form_code,
            'description': form.description,
            'last_updated': form.last_updated.isoformat()
        })
    
    return jsonify(result)
