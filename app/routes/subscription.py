from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, session
from flask_login import login_required, current_user
from app.models.subscription_models import Subscription, Tier, Feature, TierFeature, UsageRecord, VoucherCode, DonorSubsidy
from app.models.models import Organization, User
from app import db
from datetime import datetime, timedelta
import json
import uuid
import stripe
from app.utils.security import feature_required, has_feature_access, record_feature_usage

subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/')
@login_required
def index():
    """Subscription management home page"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get active subscription
    active_subscription = Subscription.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).first()
    
    # Get all available tiers
    tiers = Tier.query.filter_by(is_active=True).order_by(Tier.price).all()
    
    # Get feature usage for active subscription
    usage_data = {}
    if active_subscription:
        # Get current month's usage
        current_month = datetime.utcnow().replace(day=1).date()
        usage_records = UsageRecord.query.filter(
            UsageRecord.subscription_id == active_subscription.id,
            UsageRecord.date >= current_month
        ).all()
        
        # Group by feature
        for record in usage_records:
            feature = Feature.query.get(record.feature_id)
            if feature.name not in usage_data:
                usage_data[feature.name] = 0
            usage_data[feature.name] += record.count
        
        # Get tier features with limits
        tier_features = TierFeature.query.filter_by(
            tier_id=active_subscription.tier_id
        ).all()
        
        # Add limits to usage data
        for tf in tier_features:
            feature = Feature.query.get(tf.feature_id)
            if feature.name not in usage_data:
                usage_data[feature.name] = 0
            
            # Add limit information
            usage_data[f"{feature.name}_limit"] = tf.usage_limit
            usage_data[f"{feature.name}_enabled"] = tf.is_enabled
    
    return render_template('subscription/index.html',
                          organization=organization,
                          active_subscription=active_subscription,
                          tiers=tiers,
                          usage_data=usage_data)

@subscription_bp.route('/tiers')
@login_required
def view_tiers():
    """View available subscription tiers"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get active subscription
    active_subscription = Subscription.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).first()
    
    # Get all available tiers
    tiers = Tier.query.filter_by(is_active=True).order_by(Tier.price).all()
    
    # Get features for each tier
    tier_features = {}
    for tier in tiers:
        features = db.session.query(Feature).join(TierFeature).filter(
            TierFeature.tier_id == tier.id,
            TierFeature.is_enabled == True
        ).all()
        
        tier_features[tier.id] = features
    
    return render_template('subscription/tiers.html',
                          organization=organization,
                          active_subscription=active_subscription,
                          tiers=tiers,
                          tier_features=tier_features)

@subscription_bp.route('/subscribe/<int:tier_id>', methods=['GET', 'POST'])
@login_required
def subscribe(tier_id):
    """Subscribe to a tier"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get tier
    tier = Tier.query.get_or_404(tier_id)
    
    # Check if tier is active
    if not tier.is_active:
        flash('This subscription tier is not available.', 'warning')
        return redirect(url_for('subscription.view_tiers'))
    
    # Get active subscription
    active_subscription = Subscription.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).first()
    
    if request.method == 'POST':
        # Check for voucher code
        voucher_code = request.form.get('voucher_code')
        discount_amount = 0
        
        if voucher_code:
            # Validate voucher code
            voucher = VoucherCode.query.filter_by(
                code=voucher_code,
                is_active=True
            ).first()
            
            if voucher and voucher.expiry_date > datetime.utcnow():
                discount_amount = voucher.discount_amount
                
                # Mark voucher as used
                voucher.is_active = False
                voucher.used_by_organization_id = organization.id
                voucher.used_at = datetime.utcnow()
                
                db.session.add(voucher)
            else:
                flash('Invalid or expired voucher code.', 'danger')
                return redirect(url_for('subscription.subscribe', tier_id=tier.id))
        
        # Calculate final price
        final_price = max(0, tier.price - discount_amount)
        
        # Process payment (in a real implementation)
        # For demo purposes, simulate successful payment
        payment_successful = True
        payment_id = f"payment_{uuid.uuid4()}"
        
        if payment_successful:
            # Deactivate current subscription if exists
            if active_subscription:
                active_subscription.is_active = False
                active_subscription.ended_at = datetime.utcnow()
                db.session.add(active_subscription)
            
            # Create new subscription
            new_subscription = Subscription(
                organization_id=organization.id,
                tier_id=tier.id,
                started_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=365),  # 1 year subscription
                is_active=True,
                payment_id=payment_id,
                payment_amount=final_price,
                created_by=current_user.id
            )
            
            db.session.add(new_subscription)
            db.session.commit()
            
            flash(f'Successfully subscribed to {tier.name} tier.', 'success')
            return redirect(url_for('subscription.index'))
        else:
            flash('Payment processing failed. Please try again.', 'danger')
            return redirect(url_for('subscription.subscribe', tier_id=tier.id))
    
    return render_template('subscription/subscribe.html',
                          organization=organization,
                          tier=tier,
                          active_subscription=active_subscription)

@subscription_bp.route('/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel active subscription"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get active subscription
    active_subscription = Subscription.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).first()
    
    if not active_subscription:
        flash('No active subscription found.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Deactivate subscription
    active_subscription.is_active = False
    active_subscription.ended_at = datetime.utcnow()
    
    db.session.add(active_subscription)
    db.session.commit()
    
    flash('Subscription cancelled successfully.', 'success')
    return redirect(url_for('subscription.index'))

@subscription_bp.route('/history')
@login_required
def subscription_history():
    """View subscription history"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all subscriptions
    subscriptions = Subscription.query.filter_by(
        organization_id=organization.id
    ).order_by(Subscription.created_at.desc()).all()
    
    return render_template('subscription/history.html',
                          organization=organization,
                          subscriptions=subscriptions)

@subscription_bp.route('/usage')
@login_required
def usage_report():
    """View usage report"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get active subscription
    active_subscription = Subscription.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).first()
    
    if not active_subscription:
        flash('No active subscription found.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Get usage records for active subscription
    usage_records = UsageRecord.query.filter_by(
        subscription_id=active_subscription.id
    ).order_by(UsageRecord.date.desc()).all()
    
    # Group by feature and date
    usage_data = {}
    feature_names = {}
    
    for record in usage_records:
        feature = Feature.query.get(record.feature_id)
        feature_names[feature.id] = feature.name
        
        date_str = record.date.strftime('%Y-%m-%d')
        
        if feature.id not in usage_data:
            usage_data[feature.id] = {}
        
        usage_data[feature.id][date_str] = record.count
    
    # Get tier features with limits
    tier_features = TierFeature.query.filter_by(
        tier_id=active_subscription.tier_id
    ).all()
    
    # Create limits dictionary
    limits = {}
    for tf in tier_features:
        limits[tf.feature_id] = tf.usage_limit
    
    return render_template('subscription/usage_report.html',
                          organization=organization,
                          subscription=active_subscription,
                          usage_data=usage_data,
                          feature_names=feature_names,
                          limits=limits)

@subscription_bp.route('/apply-voucher', methods=['POST'])
@login_required
def apply_voucher():
    """Apply voucher code to get discount"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get voucher code from form
    voucher_code = request.form.get('voucher_code')
    
    if not voucher_code:
        flash('No voucher code provided.', 'danger')
        return redirect(url_for('subscription.view_tiers'))
    
    # Validate voucher code
    voucher = VoucherCode.query.filter_by(
        code=voucher_code,
        is_active=True
    ).first()
    
    if not voucher or voucher.expiry_date < datetime.utcnow():
        flash('Invalid or expired voucher code.', 'danger')
        return redirect(url_for('subscription.view_tiers'))
    
    # Store voucher in session for later use
    session['voucher_code'] = voucher_code
    
    flash(f'Voucher code applied successfully. You will receive a discount of UGX {voucher.discount_amount}.', 'success')
    return redirect(url_for('subscription.view_tiers'))

@subscription_bp.route('/donor-subsidies')
@login_required
def donor_subsidies():
    """View available donor subsidies"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get available donor subsidies
    subsidies = DonorSubsidy.query.filter_by(
        is_active=True
    ).all()
    
    # Get organization's active subsidies
    active_subsidies = DonorSubsidy.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).all()
    
    return render_template('subscription/donor_subsidies.html',
                          organization=organization,
                          subsidies=subsidies,
                          active_subsidies=active_subsidies)

@subscription_bp.route('/apply-subsidy/<int:subsidy_id>', methods=['GET', 'POST'])
@login_required
def apply_subsidy(subsidy_id):
    """Apply for donor subsidy"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get subsidy
    subsidy = DonorSubsidy.query.get_or_404(subsidy_id)
    
    # Check if subsidy is active
    if not subsidy.is_active:
        flash('This donor subsidy is not available.', 'warning')
        return redirect(url_for('subscription.donor_subsidies'))
    
    if request.method == 'POST':
        # Get application details
        reason = request.form.get('reason')
        
        if not reason:
            flash('Please provide a reason for applying.', 'danger')
            return redirect(url_for('subscription.apply_subsidy', subsidy_id=subsidy.id))
        
        # Update subsidy record
        subsidy.organization_id = organization.id
        subsidy.application_date = datetime.utcnow()
        subsidy.application_reason = reason
        subsidy.status = 'pending'
        
        db.session.add(subsidy)
        db.session.commit()
        
        flash('Subsidy application submitted successfully.', 'success')
        return redirect(url_for('subscription.donor_subsidies'))
    
    return render_template('subscription/apply_subsidy.html',
                          organization=organization,
                          subsidy=subsidy)

@subscription_bp.route('/freemium')
@login_required
def freemium():
    """Activate freemium tier"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get active subscription
    active_subscription = Subscription.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).first()
    
    # Get freemium tier
    freemium_tier = Tier.query.filter_by(
        name='Freemium',
        is_active=True
    ).first()
    
    if not freemium_tier:
        flash('Freemium tier is not available.', 'warning')
        return redirect(url_for('subscription.view_tiers'))
    
    # Deactivate current subscription if exists
    if active_subscription:
        active_subscription.is_active = False
        active_subscription.ended_at = datetime.utcnow()
        db.session.add(active_subscription)
    
    # Create new freemium subscription
    new_subscription = Subscription(
        organization_id=organization.id,
        tier_id=freemium_tier.id,
        started_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=365),  # 1 year subscription
        is_active=True,
        payment_id=None,
        payment_amount=0,
        created_by=current_user.id
    )
    
    db.session.add(new_subscription)
    db.session.commit()
    
    flash('Freemium tier activated successfully.', 'success')
    return redirect(url_for('subscription.index'))

# Helper function to record feature usage
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
