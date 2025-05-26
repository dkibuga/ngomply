from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, send_file
from flask_login import login_required, current_user
from app.models.models import Document, Organization
from app.forms.registration_forms import DocumentUploadForm, OrganizationRegistrationForm
from app import db
from app.utils.file_handlers import save_file, allowed_file, create_organization_upload_folder
import os
from datetime import datetime

registration_bp = Blueprint('registration', __name__)

@registration_bp.route('/')
@login_required
def index():
    """Registration module home page"""
    # Get user's organization if they have one
    organization = None
    if current_user.organization_id:
        organization = Organization.query.get(current_user.organization_id)
    
    return render_template('registration/index.html', organization=organization)

@registration_bp.route('/register_organization', methods=['GET', 'POST'])
@login_required
def register_organization():
    """Register a new organization"""
    # Check if user already has an organization
    if current_user.organization_id:
        flash('You are already associated with an organization.', 'warning')
        return redirect(url_for('registration.index'))
    
    form = OrganizationRegistrationForm()
    if form.validate_on_submit():
        organization = Organization(
            name=form.name.data,
            org_type=form.org_type.data,
            ngo_type=form.ngo_type.data if form.org_type.data == 'NGO' else None,
            address=form.address.data,
            phone=form.phone.data,
            email=form.email.data
        )
        db.session.add(organization)
        db.session.commit()
        
        # Associate user with organization
        current_user.organization_id = organization.id
        db.session.commit()
        
        # Create upload folder for organization
        create_organization_upload_folder(organization.id)
        
        flash('Organization registered successfully!', 'success')
        return redirect(url_for('registration.steps'))
    
    return render_template('registration/register_organization.html', form=form)

@registration_bp.route('/steps')
@login_required
def steps():
    """Registration steps guide"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    return render_template('registration/steps.html', organization=organization)

@registration_bp.route('/checklist')
@login_required
def checklist():
    """Registration checklist"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get documents uploaded by the organization
    documents = Document.query.filter_by(organization_id=organization.id).all()
    
    # Create a checklist of required documents based on organization type
    required_documents = []
    if organization.org_type == 'NGO':
        required_documents = [
            {'name': 'Certificate of Incorporation', 'uploaded': False},
            {'name': 'Memorandum and Articles of Association', 'uploaded': False},
            {'name': 'Organization Constitution', 'uploaded': False},
            {'name': 'Form A (Application for Registration)', 'uploaded': False},
            {'name': 'Form D (Recommendation by DNMC)', 'uploaded': False},
            {'name': 'Annual Work Plan', 'uploaded': False},
            {'name': 'Budget', 'uploaded': False},
            {'name': 'Minutes of General Assembly', 'uploaded': False}
        ]
    else:  # CBO
        required_documents = [
            {'name': 'Organization Constitution', 'uploaded': False},
            {'name': 'List of Founding Members', 'uploaded': False},
            {'name': 'Minutes of Election Meeting', 'uploaded': False},
            {'name': 'Work Plan', 'uploaded': False},
            {'name': 'Budget', 'uploaded': False},
            {'name': 'LC1 Recommendation Letter', 'uploaded': False},
            {'name': 'LC3 Recommendation Letter', 'uploaded': False}
        ]
    
    # Mark documents as uploaded if they exist
    for doc in documents:
        for req_doc in required_documents:
            if doc.name.lower() in req_doc['name'].lower() or req_doc['name'].lower() in doc.name.lower():
                req_doc['uploaded'] = True
                req_doc['document'] = doc
                break
    
    return render_template('registration/checklist.html', 
                          organization=organization, 
                          required_documents=required_documents)

@registration_bp.route('/upload_document', methods=['GET', 'POST'])
@login_required
def upload_document():
    """Upload a document"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    form = DocumentUploadForm()
    if form.validate_on_submit():
        try:
            # Check if file is allowed
            if not allowed_file(form.document.data.filename):
                flash('File type not allowed. Please upload PDF, Word, text, or image files.', 'danger')
                return redirect(url_for('registration.upload_document'))
            
            # Save file
            org_folder = create_organization_upload_folder(current_user.organization_id)
            file_path = save_file(form.document.data, org_folder)
            
            # Create document record
            document = Document(
                name=form.name.data,
                document_type=form.document_type.data,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                file_extension=os.path.splitext(form.document.data.filename)[1].lower()[1:],
                organization_id=current_user.organization_id,
                uploaded_by=current_user.id
            )
            db.session.add(document)
            db.session.commit()
            
            flash('Document uploaded successfully!', 'success')
            return redirect(url_for('registration.document_list'))
        except Exception as e:
            current_app.logger.error(f"Error uploading document: {str(e)}")
            flash(f"Error uploading document: {str(e)}", 'danger')
    
    return render_template('registration/upload_document.html', form=form)

@registration_bp.route('/documents')
@login_required
def document_list():
    """List all documents for an organization"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    # Get documents uploaded by the organization
    documents = Document.query.filter_by(organization_id=current_user.organization_id).all()
    
    return render_template('registration/document_list.html', documents=documents)

@registration_bp.route('/document/<int:document_id>')
@login_required
def view_document(document_id):
    """View a document"""
    document = Document.query.get_or_404(document_id)
    
    # Check if user has permission to view this document
    if document.organization_id != current_user.organization_id and not current_user.role == 'admin':
        abort(403)
    
    # Check if file exists
    if not os.path.exists(document.file_path):
        flash('Document file not found.', 'danger')
        return redirect(url_for('registration.document_list'))
    
    # Return file
    return send_file(document.file_path, as_attachment=False)

@registration_bp.route('/document/<int:document_id>/download')
@login_required
def download_document(document_id):
    """Download a document"""
    document = Document.query.get_or_404(document_id)
    
    # Check if user has permission to download this document
    if document.organization_id != current_user.organization_id and not current_user.role == 'admin':
        abort(403)
    
    # Check if file exists
    if not os.path.exists(document.file_path):
        flash('Document file not found.', 'danger')
        return redirect(url_for('registration.document_list'))
    
    # Return file for download
    return send_file(document.file_path, as_attachment=True)

@registration_bp.route('/document/<int:document_id>/delete', methods=['POST'])
@login_required
def delete_document(document_id):
    """Delete a document"""
    document = Document.query.get_or_404(document_id)
    
    # Check if user has permission to delete this document
    if document.organization_id != current_user.organization_id and not current_user.role == 'admin':
        abort(403)
    
    try:
        # Delete file if it exists
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete document record
        db.session.delete(document)
        db.session.commit()
        
        flash('Document deleted successfully!', 'success')
    except Exception as e:
        current_app.logger.error(f"Error deleting document: {str(e)}")
        flash(f"Error deleting document: {str(e)}", 'danger')
    
    return redirect(url_for('registration.document_list'))

@registration_bp.route('/ai_document_generation')
@login_required
def ai_document_generation():
    """AI document generation page"""
    # Check if user has an organization
    organization = None
    if current_user.organization_id:
        organization = Organization.query.get(current_user.organization_id)
    
    return render_template('registration/ai_document_generation.html', organization=organization)
