from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, send_file
from flask_login import login_required, current_user
from app.models.models import Organization, Document
from app import db
from datetime import datetime, timedelta
import os

permit_renewal_bp = Blueprint('permit_renewal', __name__)

@permit_renewal_bp.route('/')
@login_required
def index():
    """Permit renewal module home page"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Calculate days until permit expiry
    days_until_expiry = None
    permit_status = "Unknown"
    
    if organization.permit_expiry_date:
        today = datetime.utcnow().date()
        expiry_date = organization.permit_expiry_date.date()
        days_until_expiry = (expiry_date - today).days
        
        if days_until_expiry < 0:
            permit_status = "Expired"
        elif days_until_expiry <= 30:
            permit_status = "Expiring Soon"
        elif days_until_expiry <= 90:
            permit_status = "Renewal Recommended"
        else:
            permit_status = "Valid"
    
    return render_template('permit_renewal/index.html', 
                          organization=organization,
                          days_until_expiry=days_until_expiry,
                          permit_status=permit_status)

@permit_renewal_bp.route('/status')
@login_required
def status():
    """Check permit status"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Calculate days until permit expiry
    days_until_expiry = None
    permit_status = "Unknown"
    renewal_timeline = []
    
    if organization.permit_expiry_date:
        today = datetime.utcnow().date()
        expiry_date = organization.permit_expiry_date.date()
        days_until_expiry = (expiry_date - today).days
        
        if days_until_expiry < 0:
            permit_status = "Expired"
            renewal_timeline = [
                {"days": "Immediately", "action": "Submit renewal application as soon as possible"},
                {"days": "Within 7 days", "action": "Follow up with NGO Bureau on application status"},
                {"days": "Within 14 days", "action": "Request expedited processing if necessary"}
            ]
        elif days_until_expiry <= 30:
            permit_status = "Expiring Soon"
            renewal_timeline = [
                {"days": "Immediately", "action": "Submit renewal application"},
                {"days": "Within 7 days", "action": "Confirm receipt of application"},
                {"days": "Within 30 days", "action": "Follow up on application status"}
            ]
        elif days_until_expiry <= 90:
            permit_status = "Renewal Recommended"
            renewal_timeline = [
                {"days": "Now", "action": "Begin gathering required documents"},
                {"days": "Within 30 days", "action": "Complete and review application"},
                {"days": "Within 60 days", "action": "Submit renewal application"}
            ]
        else:
            permit_status = "Valid"
            renewal_timeline = [
                {"days": f"{days_until_expiry - 90} days before expiry", "action": "Begin gathering required documents"},
                {"days": f"{days_until_expiry - 60} days before expiry", "action": "Complete and review application"},
                {"days": f"{days_until_expiry - 30} days before expiry", "action": "Submit renewal application"}
            ]
    
    return render_template('permit_renewal/status.html', 
                          organization=organization,
                          days_until_expiry=days_until_expiry,
                          permit_status=permit_status,
                          renewal_timeline=renewal_timeline)

@permit_renewal_bp.route('/update_permit_info', methods=['GET', 'POST'])
@login_required
def update_permit_info():
    """Update permit information"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    if request.method == 'POST':
        try:
            registration_number = request.form.get('registration_number')
            permit_expiry_date_str = request.form.get('permit_expiry_date')
            
            # Update organization
            organization.registration_number = registration_number
            
            # Parse and update expiry date if provided
            if permit_expiry_date_str:
                organization.permit_expiry_date = datetime.strptime(permit_expiry_date_str, '%Y-%m-%d')
            
            db.session.commit()
            flash('Permit information updated successfully!', 'success')
            return redirect(url_for('permit_renewal.status'))
        except Exception as e:
            current_app.logger.error(f"Error updating permit info: {str(e)}")
            flash(f"Error updating permit information: {str(e)}", 'danger')
    
    return render_template('permit_renewal/update_permit_info.html', organization=organization)

@permit_renewal_bp.route('/checklist')
@login_required
def checklist():
    """Renewal document checklist"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get documents uploaded by the organization
    documents = Document.query.filter_by(organization_id=organization.id).all()
    
    # Create a checklist of required documents for renewal
    required_documents = []
    if organization.org_type == 'NGO':
        required_documents = [
            {'name': 'Form H (Application for Renewal)', 'uploaded': False},
            {'name': 'Copy of Current Permit', 'uploaded': False},
            {'name': 'Annual Reports', 'uploaded': False},
            {'name': 'Audited Financial Statements', 'uploaded': False},
            {'name': 'Updated Work Plan', 'uploaded': False},
            {'name': 'Updated Budget', 'uploaded': False},
            {'name': 'Tax Clearance Certificate', 'uploaded': False},
            {'name': 'Proof of Payment of Renewal Fees', 'uploaded': False}
        ]
    else:  # CBO
        required_documents = [
            {'name': 'Renewal Application Form', 'uploaded': False},
            {'name': 'Copy of Current Certificate', 'uploaded': False},
            {'name': 'Annual Report', 'uploaded': False},
            {'name': 'Financial Statement', 'uploaded': False},
            {'name': 'Updated Work Plan', 'uploaded': False},
            {'name': 'Updated Budget', 'uploaded': False},
            {'name': 'Proof of Payment of Renewal Fees', 'uploaded': False}
        ]
    
    # Mark documents as uploaded if they exist
    for doc in documents:
        for req_doc in required_documents:
            if doc.name.lower() in req_doc['name'].lower() or req_doc['name'].lower() in doc.name.lower():
                req_doc['uploaded'] = True
                req_doc['document'] = doc
                break
    
    return render_template('permit_renewal/checklist.html', 
                          organization=organization, 
                          required_documents=required_documents)

@permit_renewal_bp.route('/document_aggregation')
@login_required
def document_aggregation():
    """Aggregate documents for renewal"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get documents uploaded by the organization
    documents = Document.query.filter_by(organization_id=organization.id).all()
    
    # Group documents by type
    document_groups = {}
    for doc in documents:
        if doc.document_type not in document_groups:
            document_groups[doc.document_type] = []
        document_groups[doc.document_type].append(doc)
    
    return render_template('permit_renewal/document_aggregation.html', 
                          organization=organization, 
                          document_groups=document_groups)

@permit_renewal_bp.route('/fee_information')
@login_required
def fee_information():
    """Display fee information"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Set fee information based on organization type
    fee_info = {}
    if organization.org_type == 'NGO':
        if organization.ngo_type == 'Indigenous':
            fee_info = {
                'amount': 'UGX 80,000',
                'payment_method': 'Bank transfer to NGO Bureau account',
                'account_name': 'NGO Bureau',
                'account_number': '1234567890',
                'bank': 'Bank of Uganda',
                'reference': f'Permit Renewal - {organization.name}'
            }
        elif organization.ngo_type == 'Foreign':
            fee_info = {
                'amount': 'USD 100',
                'payment_method': 'Bank transfer to NGO Bureau account',
                'account_name': 'NGO Bureau',
                'account_number': '0987654321',
                'bank': 'Bank of Uganda',
                'reference': f'Permit Renewal - {organization.name}'
            }
        elif organization.ngo_type == 'International':
            fee_info = {
                'amount': 'USD 300',
                'payment_method': 'Bank transfer to NGO Bureau account',
                'account_name': 'NGO Bureau',
                'account_number': '0987654321',
                'bank': 'Bank of Uganda',
                'reference': f'Permit Renewal - {organization.name}'
            }
        else:  # Regional or Continental
            fee_info = {
                'amount': 'USD 200',
                'payment_method': 'Bank transfer to NGO Bureau account',
                'account_name': 'NGO Bureau',
                'account_number': '0987654321',
                'bank': 'Bank of Uganda',
                'reference': f'Permit Renewal - {organization.name}'
            }
    else:  # CBO
        fee_info = {
            'amount': 'UGX 30,000 - 50,000 (varies by district)',
            'payment_method': 'Payment to District Community Development Office',
            'reference': f'CBO Renewal - {organization.name}'
        }
    
    return render_template('permit_renewal/fee_information.html', 
                          organization=organization, 
                          fee_info=fee_info)

@permit_renewal_bp.route('/wizard')
@login_required
def wizard():
    """Step-by-step renewal wizard"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get documents uploaded by the organization
    documents = Document.query.filter_by(organization_id=organization.id).all()
    
    # Create a checklist of required documents for renewal
    required_documents = []
    if organization.org_type == 'NGO':
        required_documents = [
            {'name': 'Form H (Application for Renewal)', 'uploaded': False},
            {'name': 'Copy of Current Permit', 'uploaded': False},
            {'name': 'Annual Reports', 'uploaded': False},
            {'name': 'Audited Financial Statements', 'uploaded': False},
            {'name': 'Updated Work Plan', 'uploaded': False},
            {'name': 'Updated Budget', 'uploaded': False},
            {'name': 'Tax Clearance Certificate', 'uploaded': False},
            {'name': 'Proof of Payment of Renewal Fees', 'uploaded': False}
        ]
    else:  # CBO
        required_documents = [
            {'name': 'Renewal Application Form', 'uploaded': False},
            {'name': 'Copy of Current Certificate', 'uploaded': False},
            {'name': 'Annual Report', 'uploaded': False},
            {'name': 'Financial Statement', 'uploaded': False},
            {'name': 'Updated Work Plan', 'uploaded': False},
            {'name': 'Updated Budget', 'uploaded': False},
            {'name': 'Proof of Payment of Renewal Fees', 'uploaded': False}
        ]
    
    # Mark documents as uploaded if they exist
    for doc in documents:
        for req_doc in required_documents:
            if doc.name.lower() in req_doc['name'].lower() or req_doc['name'].lower() in doc.name.lower():
                req_doc['uploaded'] = True
                req_doc['document'] = doc
                break
    
    # Calculate completion percentage
    uploaded_count = sum(1 for doc in required_documents if doc['uploaded'])
    completion_percentage = int((uploaded_count / len(required_documents)) * 100)
    
    return render_template('permit_renewal/wizard.html', 
                          organization=organization, 
                          required_documents=required_documents,
                          completion_percentage=completion_percentage)
