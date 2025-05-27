from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, session, abort
from flask_login import login_required, current_user, logout_user
from app.models.models import Organization, User, Document
from app.models.subscription_models import Subscription, Feature, UsageRecord, TierFeature, Tier
from app import db
from datetime import datetime, timedelta
import os
import json
import uuid
from functools import wraps
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import hashlib

security_bp = Blueprint('security', __name__)

# Session management
@security_bp.route('/session/status')
@login_required
def session_status():
    """Check session status"""
    return jsonify({
        'active': True,
        'expires_at': session.get('expires_at', None),
        'last_activity': session.get('last_activity', None)
    })

@security_bp.route('/session/extend', methods=['POST'])
@login_required
def extend_session():
    """Extend session timeout"""
    # Update session expiry
    session['last_activity'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    session_timeout = current_app.config.get('SESSION_TIMEOUT', 30)  # Default 30 minutes
    session['expires_at'] = (datetime.utcnow() + timedelta(minutes=session_timeout)).strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({'success': True, 'expires_at': session['expires_at']})

@security_bp.route('/session/rotate', methods=['POST'])
@login_required
def rotate_session():
    """Rotate session ID for security"""
    # Store important session data
    user_id = current_user.id
    org_id = current_user.organization_id
    
    # Regenerate session
    session.clear()
    session.regenerate()
    
    # Restore important data
    session['user_id'] = user_id
    session['org_id'] = org_id
    session['last_activity'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    session_timeout = current_app.config.get('SESSION_TIMEOUT', 30)
    session['expires_at'] = (datetime.utcnow() + timedelta(minutes=session_timeout)).strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({'success': True})

# Concurrent session management
@security_bp.route('/session/validate', methods=['POST'])
@login_required
def validate_session():
    """Validate session is allowed based on subscription limits"""
    # Get user's organization
    if not current_user.organization_id:
        return jsonify({'valid': False, 'reason': 'No organization associated with user'})
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get active subscription
    subscription = Subscription.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).first()
    
    if not subscription:
        return jsonify({'valid': False, 'reason': 'No active subscription'})
    
    # Get tier
    tier = Tier.query.get(subscription.tier_id)
    
    if not tier:
        return jsonify({'valid': False, 'reason': 'Invalid subscription tier'})
    
    # Check concurrent session limit
    active_sessions = get_active_sessions(organization.id)
    
    if len(active_sessions) > tier.max_concurrent_sessions:
        # Too many sessions, check if this is the oldest one
        current_session_id = session.get('id', None)
        
        if current_session_id and current_session_id == get_oldest_session(active_sessions):
            # This is the oldest session, invalidate it
            return jsonify({'valid': False, 'reason': 'Session limit exceeded'})
    
    # Session is valid
    return jsonify({'valid': True})

# Document watermarking
@security_bp.route('/document/watermark', methods=['POST'])
@login_required
def watermark_document():
    """Add watermark to document"""
    # Check if user has an organization
    if not current_user.organization_id:
        return jsonify({'success': False, 'error': 'No organization associated with user'})
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get document ID from request
    document_id = request.json.get('document_id')
    
    if not document_id:
        return jsonify({'success': False, 'error': 'No document ID provided'})
    
    # Get document
    document = Document.query.get(document_id)
    
    if not document:
        return jsonify({'success': False, 'error': 'Document not found'})
    
    # Check if document belongs to user's organization
    if document.organization_id != organization.id:
        return jsonify({'success': False, 'error': 'Access denied'})
    
    # Get document file path
    file_path = document.file_path
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'Document file not found'})
    
    # Determine file type
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Apply watermark based on file type
    try:
        if file_ext in ['.jpg', '.jpeg', '.png']:
            watermarked_path = add_image_watermark(file_path, organization.name)
        elif file_ext == '.pdf':
            watermarked_path = add_pdf_watermark(file_path, organization.name)
        else:
            return jsonify({'success': False, 'error': 'Unsupported file type for watermarking'})
        
        # Update document record with watermarked file path
        document.watermarked_file_path = watermarked_path
        document.is_watermarked = True
        document.watermarked_at = datetime.utcnow()
        
        db.session.add(document)
        db.session.commit()
        
        return jsonify({'success': True, 'watermarked_path': watermarked_path})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Document unique identifier
@security_bp.route('/document/add-identifier', methods=['POST'])
@login_required
def add_document_identifier():
    """Add unique identifier to document"""
    # Check if user has an organization
    if not current_user.organization_id:
        return jsonify({'success': False, 'error': 'No organization associated with user'})
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get document ID from request
    document_id = request.json.get('document_id')
    
    if not document_id:
        return jsonify({'success': False, 'error': 'No document ID provided'})
    
    # Get document
    document = Document.query.get(document_id)
    
    if not document:
        return jsonify({'success': False, 'error': 'Document not found'})
    
    # Check if document belongs to user's organization
    if document.organization_id != organization.id:
        return jsonify({'success': False, 'error': 'Access denied'})
    
    # Generate unique identifier
    unique_id = generate_document_identifier(document, organization)
    
    # Update document record
    document.unique_identifier = unique_id
    document.identifier_added_at = datetime.utcnow()
    
    db.session.add(document)
    db.session.commit()
    
    return jsonify({'success': True, 'unique_identifier': unique_id})

# Usage monitoring
@security_bp.route('/usage/check-limits', methods=['POST'])
@login_required
def check_usage_limits():
    """Check if usage is within subscription limits"""
    # Check if user has an organization
    if not current_user.organization_id:
        return jsonify({'within_limits': False, 'error': 'No organization associated with user'})
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get feature name from request
    feature_name = request.json.get('feature')
    
    if not feature_name:
        return jsonify({'within_limits': False, 'error': 'No feature specified'})
    
    # Get active subscription
    subscription = Subscription.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).first()
    
    if not subscription:
        return jsonify({'within_limits': False, 'error': 'No active subscription'})
    
    # Get feature
    feature = Feature.query.filter_by(name=feature_name).first()
    
    if not feature:
        return jsonify({'within_limits': False, 'error': 'Invalid feature'})
    
    # Get tier feature
    tier_feature = db.session.query(TierFeature).filter(
        TierFeature.tier_id == subscription.tier_id,
        TierFeature.feature_id == feature.id
    ).first()
    
    if not tier_feature:
        return jsonify({'within_limits': False, 'error': 'Feature not available in subscription tier'})
    
    if not tier_feature.is_enabled:
        return jsonify({'within_limits': False, 'error': 'Feature not enabled in subscription tier'})
    
    # Check usage limits
    if tier_feature.usage_limit is not None:
        # Get current month's usage
        current_month = datetime.utcnow().replace(day=1).date()
        month_usage = db.session.query(db.func.sum(UsageRecord.count)).filter(
            UsageRecord.subscription_id == subscription.id,
            UsageRecord.feature_id == feature.id,
            UsageRecord.date >= current_month
        ).scalar() or 0
        
        if month_usage >= tier_feature.usage_limit:
            return jsonify({
                'within_limits': False, 
                'error': 'Usage limit exceeded',
                'current_usage': month_usage,
                'limit': tier_feature.usage_limit
            })
    
    # Within limits
    return jsonify({'within_limits': True})

# Account verification
@security_bp.route('/verify-ngo-registration', methods=['POST'])
@login_required
def verify_ngo_registration():
    """Verify NGO registration with URSB/NGO Bureau"""
    # Check if user has an organization
    if not current_user.organization_id:
        return jsonify({'verified': False, 'error': 'No organization associated with user'})
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get registration details from request
    registration_number = request.json.get('registration_number')
    registration_authority = request.json.get('registration_authority')
    
    if not registration_number or not registration_authority:
        return jsonify({'verified': False, 'error': 'Missing registration details'})
    
    # In a real implementation, this would call the URSB/NGO Bureau API
    # For demo purposes, simulate verification
    verification_result = simulate_ngo_verification(registration_number, registration_authority)
    
    if verification_result['verified']:
        # Update organization record
        organization.registration_verified = True
        organization.verification_date = datetime.utcnow()
        organization.verification_authority = registration_authority
        organization.verification_details = json.dumps(verification_result)
        
        db.session.add(organization)
        db.session.commit()
    
    return jsonify(verification_result)

# Helper functions
def get_active_sessions(organization_id):
    """Get active sessions for an organization"""
    # In a real implementation, this would query a session store
    # For demo purposes, return a simulated list
    return [
        {'id': 'session1', 'user_id': 1, 'created_at': datetime.utcnow() - timedelta(hours=1)},
        {'id': 'session2', 'user_id': 2, 'created_at': datetime.utcnow() - timedelta(minutes=30)}
    ]

def get_oldest_session(sessions):
    """Get the ID of the oldest session"""
    if not sessions:
        return None
    
    oldest = min(sessions, key=lambda s: s['created_at'])
    return oldest['id']

def add_image_watermark(image_path, org_name):
    """Add watermark to image"""
    # Open image
    img = Image.open(image_path)
    
    # Create transparent overlay
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Load font
    try:
        font = ImageFont.truetype('arial.ttf', 40)
    except IOError:
        font = ImageFont.load_default()
    
    # Create watermark text
    watermark_text = f"NGOmply - {org_name} - {datetime.utcnow().strftime('%Y-%m-%d')}"
    
    # Calculate text size
    text_width, text_height = draw.textsize(watermark_text, font=font)
    
    # Calculate position (diagonal across image)
    position = ((img.width - text_width) // 2, (img.height - text_height) // 2)
    
    # Draw watermark
    draw.text(position, watermark_text, font=font, fill=(255, 255, 255, 128))
    
    # Rotate watermark
    rotated_overlay = overlay.rotate(45, expand=1)
    
    # Resize rotated overlay to match original image
    rotated_overlay = rotated_overlay.resize(img.size)
    
    # Composite images
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    watermarked = Image.alpha_composite(img, rotated_overlay)
    
    # Save watermarked image
    watermarked_path = f"{os.path.splitext(image_path)[0]}_watermarked{os.path.splitext(image_path)[1]}"
    watermarked.save(watermarked_path)
    
    return watermarked_path

def add_pdf_watermark(pdf_path, org_name):
    """Add watermark to PDF"""
    # In a real implementation, this would use a PDF library like PyPDF2
    # For demo purposes, return the original path
    return pdf_path

def generate_document_identifier(document, organization):
    """Generate unique identifier for document"""
    # Create base string from document and organization data
    base_string = f"{document.id}_{organization.id}_{document.created_at}_{uuid.uuid4()}"
    
    # Create hash
    hash_object = hashlib.sha256(base_string.encode())
    hash_hex = hash_object.hexdigest()
    
    # Format as readable identifier
    identifier = f"NGO-{organization.id}-DOC-{document.id}-{hash_hex[:8]}"
    
    return identifier

def simulate_ngo_verification(registration_number, authority):
    """Simulate NGO registration verification"""
    # In a real implementation, this would call the URSB/NGO Bureau API
    # For demo purposes, simulate verification
    
    # Simulate successful verification for specific test numbers
    if registration_number in ['NGO12345', 'CBO54321', 'URSB98765']:
        return {
            'verified': True,
            'organization_name': 'Test Organization',
            'registration_date': '2020-01-01',
            'status': 'Active',
            'authority': authority
        }
    
    # Simulate failed verification
    return {
        'verified': False,
        'error': 'Registration number not found',
        'authority': authority
    }

# Decorators for feature access control
def feature_required(feature_name):
    """Decorator to check if user has access to a feature"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is logged in
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Check if user has an organization
            if not current_user.organization_id:
                flash('You need to register an organization first.', 'warning')
                return redirect(url_for('registration.register_organization'))
            
            # Check feature access
            if not has_feature_access(current_user.organization_id, feature_name):
                flash(f'This feature is not available in your current subscription tier.', 'warning')
                return redirect(url_for('subscription.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def has_feature_access(organization_id, feature_name):
    """Check if organization has access to a feature based on subscription tier"""
    # Get active subscription
    subscription = Subscription.query.filter_by(
        organization_id=organization_id,
        is_active=True
    ).first()
    
    if not subscription:
        return False
    
    # Get feature
    feature = Feature.query.filter_by(name=feature_name).first()
    
    if not feature:
        return False
    
    # Check if feature is enabled for tier
    tier_feature = db.session.query(TierFeature).filter(
        TierFeature.tier_id == subscription.tier_id,
        TierFeature.feature_id == feature.id,
        TierFeature.is_enabled == True
    ).first()
    
    return tier_feature is not None
