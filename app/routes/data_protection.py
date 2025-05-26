from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app.models.data_protection_models import DataProtectionAssessment, ConsentRecord, DataBreachRecord, PDPORegistration, DataProtectionPolicy
from app.models.models import Organization, User, Document
from app.models.subscription_models import Subscription, Feature, UsageRecord
from app import db
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from app.utils.file_handlers import allowed_file, save_file

data_protection_bp = Blueprint('data_protection', __name__)

@data_protection_bp.route('/')
@login_required
def index():
    """Data Protection Compliance Module home page"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get PDPO registration status
    pdpo_registration = PDPORegistration.query.filter_by(organization_id=organization.id).first()
    
    # Get recent assessments
    assessments = DataProtectionAssessment.query.filter_by(
        organization_id=organization.id
    ).order_by(DataProtectionAssessment.created_at.desc()).limit(5).all()
    
    # Get recent data breaches
    breaches = DataBreachRecord.query.filter_by(
        organization_id=organization.id
    ).order_by(DataBreachRecord.created_at.desc()).limit(5).all()
    
    # Get active policies
    policies = DataProtectionPolicy.query.filter_by(
        organization_id=organization.id,
        status='active'
    ).order_by(DataProtectionPolicy.effective_date.desc()).all()
    
    # Calculate compliance score
    compliance_score = calculate_data_protection_compliance_score(organization.id)
    
    return render_template('data_protection/index.html',
                          organization=organization,
                          pdpo_registration=pdpo_registration,
                          assessments=assessments,
                          breaches=breaches,
                          policies=policies,
                          compliance_score=compliance_score)

@data_protection_bp.route('/pdpo-registration', methods=['GET', 'POST'])
@login_required
def pdpo_registration():
    """Manage PDPO registration"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get or create PDPO registration
    registration = PDPORegistration.query.filter_by(organization_id=organization.id).first()
    if not registration:
        registration = PDPORegistration(organization_id=organization.id)
        db.session.add(registration)
        db.session.commit()
    
    if request.method == 'POST':
        registration_number = request.form.get('registration_number')
        registration_date_str = request.form.get('registration_date')
        renewal_date_str = request.form.get('renewal_date')
        status = request.form.get('status')
        annual_report_submitted = request.form.get('annual_report_submitted') == 'on'
        last_report_date_str = request.form.get('last_report_date')
        
        # Parse dates
        registration_date = None
        if registration_date_str:
            try:
                registration_date = datetime.strptime(registration_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid registration date format.', 'danger')
                return redirect(url_for('data_protection.pdpo_registration'))
        
        renewal_date = None
        if renewal_date_str:
            try:
                renewal_date = datetime.strptime(renewal_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid renewal date format.', 'danger')
                return redirect(url_for('data_protection.pdpo_registration'))
        
        last_report_date = None
        if last_report_date_str:
            try:
                last_report_date = datetime.strptime(last_report_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid last report date format.', 'danger')
                return redirect(url_for('data_protection.pdpo_registration'))
        
        # Update registration
        registration.registration_number = registration_number
        registration.registration_date = registration_date
        registration.renewal_date = renewal_date
        registration.status = status
        registration.annual_report_submitted = annual_report_submitted
        registration.last_report_date = last_report_date
        
        db.session.add(registration)
        db.session.commit()
        
        flash('PDPO registration information updated successfully.', 'success')
        return redirect(url_for('data_protection.index'))
    
    return render_template('data_protection/pdpo_registration.html',
                          organization=organization,
                          registration=registration)

@data_protection_bp.route('/assessments')
@login_required
def assessments():
    """View data protection impact assessments"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all assessments
    assessments = DataProtectionAssessment.query.filter_by(
        organization_id=organization.id
    ).order_by(DataProtectionAssessment.created_at.desc()).all()
    
    return render_template('data_protection/assessments.html',
                          organization=organization,
                          assessments=assessments)

@data_protection_bp.route('/assessments/new', methods=['GET', 'POST'])
@login_required
def new_assessment():
    """Create new data protection impact assessment"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'data_protection_assessment'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        processing_purpose = request.form.get('processing_purpose')
        data_categories = request.form.get('data_categories')
        data_subjects = request.form.get('data_subjects')
        risk_assessment = request.form.get('risk_assessment')
        mitigation_measures = request.form.get('mitigation_measures')
        status = request.form.get('status', 'draft')
        
        # Create assessment
        assessment = DataProtectionAssessment(
            organization_id=organization.id,
            title=title,
            description=description,
            processing_purpose=processing_purpose,
            data_categories=data_categories,
            data_subjects=data_subjects,
            risk_assessment=risk_assessment,
            mitigation_measures=mitigation_measures,
            status=status,
            created_by=current_user.id
        )
        
        if status == 'completed':
            assessment.completed_date = datetime.utcnow()
        
        db.session.add(assessment)
        
        # Record feature usage
        record_feature_usage(organization.id, 'data_protection_assessment')
        
        db.session.commit()
        
        flash('Data Protection Impact Assessment created successfully.', 'success')
        return redirect(url_for('data_protection.assessments'))
    
    return render_template('data_protection/new_assessment.html',
                          organization=organization)

@data_protection_bp.route('/assessments/<int:assessment_id>')
@login_required
def view_assessment(assessment_id):
    """View a data protection impact assessment"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get assessment
    assessment = DataProtectionAssessment.query.get_or_404(assessment_id)
    
    # Check if assessment belongs to user's organization
    if assessment.organization_id != organization.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('data_protection.assessments'))
    
    return render_template('data_protection/view_assessment.html',
                          organization=organization,
                          assessment=assessment)

@data_protection_bp.route('/consent-records')
@login_required
def consent_records():
    """View consent records"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all consent records
    records = ConsentRecord.query.filter_by(
        organization_id=organization.id
    ).order_by(ConsentRecord.created_at.desc()).all()
    
    return render_template('data_protection/consent_records.html',
                          organization=organization,
                          records=records)

@data_protection_bp.route('/consent-records/new', methods=['GET', 'POST'])
@login_required
def new_consent_record():
    """Create new consent record"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'consent_management'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        subject_name = request.form.get('subject_name')
        subject_identifier = request.form.get('subject_identifier')
        purpose = request.form.get('purpose')
        consent_given = request.form.get('consent_given') == 'on'
        consent_date_str = request.form.get('consent_date')
        expiry_date_str = request.form.get('expiry_date')
        
        # Parse dates
        consent_date = None
        if consent_date_str:
            try:
                consent_date = datetime.strptime(consent_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid consent date format.', 'danger')
                return redirect(url_for('data_protection.new_consent_record'))
        
        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid expiry date format.', 'danger')
                return redirect(url_for('data_protection.new_consent_record'))
        
        # Handle file upload
        consent_proof_path = None
        if 'consent_proof' in request.files:
            file = request.files['consent_proof']
            if file and file.filename and allowed_file(file.filename, ['pdf', 'jpg', 'jpeg', 'png']):
                filename = secure_filename(file.filename)
                consent_proof_path = save_file(file, 'consent_proofs', filename)
        
        # Create consent record
        record = ConsentRecord(
            organization_id=organization.id,
            subject_name=subject_name,
            subject_identifier=subject_identifier,
            purpose=purpose,
            consent_given=consent_given,
            consent_date=consent_date,
            expiry_date=expiry_date,
            consent_proof=consent_proof_path,
            created_by=current_user.id
        )
        
        db.session.add(record)
        
        # Record feature usage
        record_feature_usage(organization.id, 'consent_management')
        
        db.session.commit()
        
        flash('Consent record created successfully.', 'success')
        return redirect(url_for('data_protection.consent_records'))
    
    return render_template('data_protection/new_consent_record.html',
                          organization=organization)

@data_protection_bp.route('/data-breaches')
@login_required
def data_breaches():
    """View data breach records"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all data breach records
    breaches = DataBreachRecord.query.filter_by(
        organization_id=organization.id
    ).order_by(DataBreachRecord.created_at.desc()).all()
    
    return render_template('data_protection/data_breaches.html',
                          organization=organization,
                          breaches=breaches)

@data_protection_bp.route('/data-breaches/new', methods=['GET', 'POST'])
@login_required
def new_data_breach():
    """Create new data breach record"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'data_breach_management'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        breach_date_str = request.form.get('breach_date')
        discovery_date_str = request.form.get('discovery_date')
        description = request.form.get('description')
        data_affected = request.form.get('data_affected')
        subjects_affected = request.form.get('subjects_affected', 0)
        risk_assessment = request.form.get('risk_assessment')
        mitigation_steps = request.form.get('mitigation_steps')
        reported_to_authority = request.form.get('reported_to_authority') == 'on'
        authority_report_date_str = request.form.get('authority_report_date')
        subjects_notified = request.form.get('subjects_notified') == 'on'
        subject_notification_date_str = request.form.get('subject_notification_date')
        status = request.form.get('status', 'open')
        
        # Parse dates
        breach_date = None
        if breach_date_str:
            try:
                breach_date = datetime.strptime(breach_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid breach date format.', 'danger')
                return redirect(url_for('data_protection.new_data_breach'))
        
        discovery_date = None
        if discovery_date_str:
            try:
                discovery_date = datetime.strptime(discovery_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid discovery date format.', 'danger')
                return redirect(url_for('data_protection.new_data_breach'))
        
        authority_report_date = None
        if authority_report_date_str:
            try:
                authority_report_date = datetime.strptime(authority_report_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid authority report date format.', 'danger')
                return redirect(url_for('data_protection.new_data_breach'))
        
        subject_notification_date = None
        if subject_notification_date_str:
            try:
                subject_notification_date = datetime.strptime(subject_notification_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid subject notification date format.', 'danger')
                return redirect(url_for('data_protection.new_data_breach'))
        
        # Create data breach record
        breach = DataBreachRecord(
            organization_id=organization.id,
            breach_date=breach_date,
            discovery_date=discovery_date,
            description=description,
            data_affected=data_affected,
            subjects_affected=int(subjects_affected),
            risk_assessment=risk_assessment,
            mitigation_steps=mitigation_steps,
            reported_to_authority=reported_to_authority,
            authority_report_date=authority_report_date,
            subjects_notified=subjects_notified,
            subject_notification_date=subject_notification_date,
            status=status,
            created_by=current_user.id
        )
        
        db.session.add(breach)
        
        # Record feature usage
        record_feature_usage(organization.id, 'data_breach_management')
        
        db.session.commit()
        
        flash('Data breach record created successfully.', 'success')
        return redirect(url_for('data_protection.data_breaches'))
    
    return render_template('data_protection/new_data_breach.html',
                          organization=organization)

@data_protection_bp.route('/policies')
@login_required
def policies():
    """View data protection policies"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all policies
    policies = DataProtectionPolicy.query.filter_by(
        organization_id=organization.id
    ).order_by(DataProtectionPolicy.created_at.desc()).all()
    
    return render_template('data_protection/policies.html',
                          organization=organization,
                          policies=policies)

@data_protection_bp.route('/policies/new', methods=['GET', 'POST'])
@login_required
def new_policy():
    """Create new data protection policy"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'data_protection_policy'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        version = request.form.get('version')
        effective_date_str = request.form.get('effective_date')
        review_date_str = request.form.get('review_date')
        status = request.form.get('status', 'draft')
        
        # Parse dates
        effective_date = None
        if effective_date_str:
            try:
                effective_date = datetime.strptime(effective_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid effective date format.', 'danger')
                return redirect(url_for('data_protection.new_policy'))
        
        review_date = None
        if review_date_str:
            try:
                review_date = datetime.strptime(review_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid review date format.', 'danger')
                return redirect(url_for('data_protection.new_policy'))
        
        # Handle file upload
        file_path = None
        if 'policy_file' in request.files:
            file = request.files['policy_file']
            if file and file.filename and allowed_file(file.filename, ['pdf', 'docx']):
                filename = secure_filename(file.filename)
                file_path = save_file(file, 'policies', filename)
        
        # Create policy
        policy = DataProtectionPolicy(
            organization_id=organization.id,
            title=title,
            content=content,
            version=version,
            effective_date=effective_date,
            review_date=review_date,
            status=status,
            file_path=file_path,
            created_by=current_user.id
        )
        
        db.session.add(policy)
        
        # Record feature usage
        record_feature_usage(organization.id, 'data_protection_policy')
        
        db.session.commit()
        
        flash('Data protection policy created successfully.', 'success')
        return redirect(url_for('data_protection.policies'))
    
    return render_template('data_protection/new_policy.html',
                          organization=organization)

@data_protection_bp.route('/compliance-report')
@login_required
def compliance_report():
    """Generate data protection compliance report"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'data_protection_report'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Get PDPO registration status
    pdpo_registration = PDPORegistration.query.filter_by(organization_id=organization.id).first()
    
    # Get assessments count
    assessments_count = DataProtectionAssessment.query.filter_by(
        organization_id=organization.id
    ).count()
    
    # Get consent records count
    consent_records_count = ConsentRecord.query.filter_by(
        organization_id=organization.id
    ).count()
    
    # Get data breaches count
    data_breaches_count = DataBreachRecord.query.filter_by(
        organization_id=organization.id
    ).count()
    
    # Get policies count
    policies_count = DataProtectionPolicy.query.filter_by(
        organization_id=organization.id,
        status='active'
    ).count()
    
    # Calculate compliance score
    compliance_score = calculate_data_protection_compliance_score(organization.id)
    
    # Record feature usage
    record_feature_usage(organization.id, 'data_protection_report')
    
    return render_template('data_protection/compliance_report.html',
                          organization=organization,
                          pdpo_registration=pdpo_registration,
                          assessments_count=assessments_count,
                          consent_records_count=consent_records_count,
                          data_breaches_count=data_breaches_count,
                          policies_count=policies_count,
                          compliance_score=compliance_score)

# Helper functions
def calculate_data_protection_compliance_score(organization_id):
    """Calculate data protection compliance score (0-100)"""
    score = 0
    
    # Check PDPO registration
    pdpo_registration = PDPORegistration.query.filter_by(organization_id=organization_id).first()
    if pdpo_registration:
        if pdpo_registration.status == 'registered':
            score += 30
        elif pdpo_registration.status == 'pending':
            score += 15
        
        if pdpo_registration.annual_report_submitted:
            score += 10
    
    # Check if has active policies
    policies = DataProtectionPolicy.query.filter_by(
        organization_id=organization_id,
        status='active'
    ).count()
    
    if policies > 0:
        score += 20
    
    # Check if has completed assessments
    assessments = DataProtectionAssessment.query.filter_by(
        organization_id=organization_id,
        status='completed'
    ).count()
    
    if assessments > 0:
        score += 20
    
    # Check if has consent records
    consent_records = ConsentRecord.query.filter_by(
        organization_id=organization_id
    ).count()
    
    if consent_records > 0:
        score += 10
    
    # Check if has properly handled data breaches
    breaches = DataBreachRecord.query.filter_by(
        organization_id=organization_id
    ).all()
    
    if breaches:
        properly_handled = all(b.reported_to_authority and b.subjects_notified for b in breaches)
        if properly_handled:
            score += 10
    else:
        # No breaches is good
        score += 10
    
    return min(score, 100)  # Cap at 100

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
