from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, session
from flask_login import login_required, current_user
from app.models.value_added_models import ConsultingService, TrainingService, ConsultingRequest, TrainingRegistration, ServiceReview
from app.models.models import Organization, User, Document
from app.models.subscription_models import Subscription, Feature, UsageRecord, TierFeature
from app import db
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from app.utils.file_handlers import allowed_file, save_file

value_added_bp = Blueprint('value_added', __name__)

@value_added_bp.route('/')
@login_required
def index():
    """Value-Added Services home page"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get available consulting services
    consulting_services = ConsultingService.query.filter_by(
        is_active=True
    ).all()
    
    # Get available training services
    training_services = TrainingService.query.filter_by(
        is_active=True
    ).all()
    
    # Get user's active requests
    consulting_requests = ConsultingRequest.query.filter_by(
        organization_id=organization.id
    ).order_by(ConsultingRequest.created_at.desc()).limit(3).all()
    
    # Get user's training registrations
    training_registrations = TrainingRegistration.query.filter_by(
        organization_id=organization.id
    ).order_by(TrainingRegistration.created_at.desc()).limit(3).all()
    
    return render_template('value_added/index.html',
                          organization=organization,
                          consulting_services=consulting_services,
                          training_services=training_services,
                          consulting_requests=consulting_requests,
                          training_registrations=training_registrations)

@value_added_bp.route('/consulting')
@login_required
def consulting():
    """View consulting services"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all consulting services
    consulting_services = ConsultingService.query.filter_by(
        is_active=True
    ).all()
    
    # Get user's subscription tier to determine pricing
    subscription = Subscription.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).first()
    
    tier_id = subscription.tier_id if subscription else None
    
    return render_template('value_added/consulting.html',
                          organization=organization,
                          consulting_services=consulting_services,
                          tier_id=tier_id)

@value_added_bp.route('/consulting/<int:service_id>')
@login_required
def view_consulting_service(service_id):
    """View consulting service details"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get service
    service = ConsultingService.query.get_or_404(service_id)
    
    # Check if service is active
    if not service.is_active:
        flash('This service is currently not available.', 'warning')
        return redirect(url_for('value_added.consulting'))
    
    # Get user's subscription tier to determine pricing
    subscription = Subscription.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).first()
    
    tier_id = subscription.tier_id if subscription else None
    
    # Get service reviews
    reviews = ServiceReview.query.filter_by(
        service_type='consulting',
        service_id=service.id
    ).order_by(ServiceReview.created_at.desc()).limit(5).all()
    
    return render_template('value_added/view_consulting_service.html',
                          organization=organization,
                          service=service,
                          tier_id=tier_id,
                          reviews=reviews)

@value_added_bp.route('/consulting/<int:service_id>/request', methods=['GET', 'POST'])
@login_required
def request_consulting(service_id):
    """Request consulting service"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get service
    service = ConsultingService.query.get_or_404(service_id)
    
    # Check if service is active
    if not service.is_active:
        flash('This service is currently not available.', 'warning')
        return redirect(url_for('value_added.consulting'))
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'consulting_services'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        description = request.form.get('description')
        preferred_date_str = request.form.get('preferred_date')
        
        # Parse date
        preferred_date = None
        if preferred_date_str:
            try:
                preferred_date = datetime.strptime(preferred_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid date format.', 'danger')
                return redirect(url_for('value_added.request_consulting', service_id=service.id))
        
        # Create request
        consulting_request = ConsultingRequest(
            organization_id=organization.id,
            service_id=service.id,
            user_id=current_user.id,
            description=description,
            preferred_date=preferred_date,
            status='pending'
        )
        
        db.session.add(consulting_request)
        
        # Record feature usage
        record_feature_usage(organization.id, 'consulting_services')
        
        db.session.commit()
        
        flash('Consulting request submitted successfully.', 'success')
        return redirect(url_for('value_added.my_consulting_requests'))
    
    return render_template('value_added/request_consulting.html',
                          organization=organization,
                          service=service)

@value_added_bp.route('/consulting/my-requests')
@login_required
def my_consulting_requests():
    """View user's consulting requests"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all requests
    requests = ConsultingRequest.query.filter_by(
        organization_id=organization.id
    ).order_by(ConsultingRequest.created_at.desc()).all()
    
    return render_template('value_added/my_consulting_requests.html',
                          organization=organization,
                          requests=requests)

@value_added_bp.route('/training')
@login_required
def training():
    """View training services"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all training services
    training_services = TrainingService.query.filter_by(
        is_active=True
    ).all()
    
    # Get user's subscription tier to determine pricing
    subscription = Subscription.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).first()
    
    tier_id = subscription.tier_id if subscription else None
    
    return render_template('value_added/training.html',
                          organization=organization,
                          training_services=training_services,
                          tier_id=tier_id)

@value_added_bp.route('/training/<int:service_id>')
@login_required
def view_training_service(service_id):
    """View training service details"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get service
    service = TrainingService.query.get_or_404(service_id)
    
    # Check if service is active
    if not service.is_active:
        flash('This service is currently not available.', 'warning')
        return redirect(url_for('value_added.training'))
    
    # Get user's subscription tier to determine pricing
    subscription = Subscription.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).first()
    
    tier_id = subscription.tier_id if subscription else None
    
    # Get service reviews
    reviews = ServiceReview.query.filter_by(
        service_type='training',
        service_id=service.id
    ).order_by(ServiceReview.created_at.desc()).limit(5).all()
    
    return render_template('value_added/view_training_service.html',
                          organization=organization,
                          service=service,
                          tier_id=tier_id,
                          reviews=reviews)

@value_added_bp.route('/training/<int:service_id>/register', methods=['GET', 'POST'])
@login_required
def register_training(service_id):
    """Register for training service"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get service
    service = TrainingService.query.get_or_404(service_id)
    
    # Check if service is active
    if not service.is_active:
        flash('This service is currently not available.', 'warning')
        return redirect(url_for('value_added.training'))
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'training_services'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        participants = request.form.get('participants')
        notes = request.form.get('notes')
        
        # Create registration
        training_registration = TrainingRegistration(
            organization_id=organization.id,
            service_id=service.id,
            user_id=current_user.id,
            participants=participants,
            notes=notes,
            status='pending'
        )
        
        db.session.add(training_registration)
        
        # Record feature usage
        record_feature_usage(organization.id, 'training_services')
        
        db.session.commit()
        
        flash('Training registration submitted successfully.', 'success')
        return redirect(url_for('value_added.my_training_registrations'))
    
    return render_template('value_added/register_training.html',
                          organization=organization,
                          service=service)

@value_added_bp.route('/training/my-registrations')
@login_required
def my_training_registrations():
    """View user's training registrations"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all registrations
    registrations = TrainingRegistration.query.filter_by(
        organization_id=organization.id
    ).order_by(TrainingRegistration.created_at.desc()).all()
    
    return render_template('value_added/my_training_registrations.html',
                          organization=organization,
                          registrations=registrations)

@value_added_bp.route('/review/<string:service_type>/<int:service_id>', methods=['GET', 'POST'])
@login_required
def review_service(service_type, service_id):
    """Submit review for a service"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Validate service type
    if service_type not in ['consulting', 'training']:
        flash('Invalid service type.', 'danger')
        return redirect(url_for('value_added.index'))
    
    # Get service
    if service_type == 'consulting':
        service = ConsultingService.query.get_or_404(service_id)
    else:
        service = TrainingService.query.get_or_404(service_id)
    
    # Check if user has used this service
    if service_type == 'consulting':
        service_used = ConsultingRequest.query.filter_by(
            organization_id=organization.id,
            service_id=service_id,
            status='completed'
        ).first()
    else:
        service_used = TrainingRegistration.query.filter_by(
            organization_id=organization.id,
            service_id=service_id,
            status='completed'
        ).first()
    
    if not service_used:
        flash('You can only review services you have used.', 'warning')
        return redirect(url_for('value_added.index'))
    
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        
        # Create review
        review = ServiceReview(
            organization_id=organization.id,
            user_id=current_user.id,
            service_type=service_type,
            service_id=service_id,
            rating=rating,
            comment=comment
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Review submitted successfully.', 'success')
        
        if service_type == 'consulting':
            return redirect(url_for('value_added.view_consulting_service', service_id=service_id))
        else:
            return redirect(url_for('value_added.view_training_service', service_id=service_id))
    
    return render_template('value_added/review_service.html',
                          organization=organization,
                          service=service,
                          service_type=service_type)

@value_added_bp.route('/audit-preparation')
@login_required
def audit_preparation():
    """Audit preparation service"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'audit_preparation'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Record feature usage
    record_feature_usage(organization.id, 'audit_preparation')
    
    return render_template('value_added/audit_preparation.html',
                          organization=organization)

@value_added_bp.route('/financial-review')
@login_required
def financial_review():
    """Financial review service"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'financial_review'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Record feature usage
    record_feature_usage(organization.id, 'financial_review')
    
    return render_template('value_added/financial_review.html',
                          organization=organization)

# Helper functions
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

def record_feature_usage(organization_id, feature_name):
    """Record usage of a feature"""
    # Get active subscription
    subscription = Subscription.query.filter_by(
        organization_id=organization_id,
        is_active=True
    ).first()
    
    if not subscription:
        return
    
    # Get feature
    feature = Feature.query.filter_by(name=feature_name).first()
    
    if not feature:
        return
    
    # Check if there's a usage record for today
    today = datetime.utcnow().date()
    usage_record = UsageRecord.query.filter_by(
        subscription_id=subscription.id,
        feature_id=feature.id,
        date=today
    ).first()
    
    if usage_record:
        # Increment count
        usage_record.count += 1
    else:
        # Create new record
        usage_record = UsageRecord(
            subscription_id=subscription.id,
            feature_id=feature.id,
            count=1,
            date=today
        )
    
    db.session.add(usage_record)
    db.session.commit()
