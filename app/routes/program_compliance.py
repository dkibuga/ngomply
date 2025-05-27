from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app.models.program_compliance_models import ProgramArea, SectorRequirement, OrganizationProgram, LocalPermit, ComplianceRisk
from app.models.models import Organization, User, Document
from app.models.subscription_models import Subscription, Feature, UsageRecord, TierFeature
from app import db
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from app.utils.file_handlers import allowed_file, save_file

program_compliance_bp = Blueprint('program_compliance', __name__)

@program_compliance_bp.route('/')
@login_required
def index():
    """Program Compliance Tracker Module home page"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get organization's program areas
    program_areas = db.session.query(ProgramArea).join(
        OrganizationProgram, OrganizationProgram.program_area_id == ProgramArea.id
    ).filter(
        OrganizationProgram.organization_id == organization.id,
        OrganizationProgram.is_active == True
    ).all()
    
    # Get local permits
    permits = LocalPermit.query.filter_by(
        organization_id=organization.id
    ).order_by(LocalPermit.expiry_date).all()
    
    # Get compliance risks
    risks = ComplianceRisk.query.filter_by(
        organization_id=organization.id
    ).order_by(ComplianceRisk.risk_level.desc()).limit(5).all()
    
    # Calculate compliance score
    compliance_score = calculate_program_compliance_score(organization.id)
    
    return render_template('program_compliance/index.html',
                          organization=organization,
                          program_areas=program_areas,
                          permits=permits,
                          risks=risks,
                          compliance_score=compliance_score)

@program_compliance_bp.route('/program-areas')
@login_required
def program_areas():
    """View program areas"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get organization's program areas
    org_programs = OrganizationProgram.query.filter_by(
        organization_id=organization.id
    ).all()
    
    # Get all available program areas
    all_program_areas = ProgramArea.query.all()
    
    return render_template('program_compliance/program_areas.html',
                          organization=organization,
                          org_programs=org_programs,
                          all_program_areas=all_program_areas)

@program_compliance_bp.route('/program-areas/add', methods=['GET', 'POST'])
@login_required
def add_program_area():
    """Add program area to organization"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'program_compliance_tracking'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        program_area_id = request.form.get('program_area_id')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        
        # Parse dates
        start_date = datetime.utcnow()
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid start date format.', 'danger')
                return redirect(url_for('program_compliance.add_program_area'))
        
        end_date = None
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid end date format.', 'danger')
                return redirect(url_for('program_compliance.add_program_area'))
        
        # Check if already added
        existing = OrganizationProgram.query.filter_by(
            organization_id=organization.id,
            program_area_id=program_area_id
        ).first()
        
        if existing:
            # Update existing
            existing.start_date = start_date
            existing.end_date = end_date
            existing.is_active = True
            db.session.add(existing)
        else:
            # Create new association
            org_program = OrganizationProgram(
                organization_id=organization.id,
                program_area_id=program_area_id,
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )
            db.session.add(org_program)
        
        # Record feature usage
        record_feature_usage(organization.id, 'program_compliance_tracking')
        
        db.session.commit()
        
        flash('Program area added successfully.', 'success')
        return redirect(url_for('program_compliance.program_areas'))
    
    # Get all available program areas
    program_areas = ProgramArea.query.all()
    
    # Get already added program areas
    added_program_areas = db.session.query(ProgramArea.id).join(
        OrganizationProgram, OrganizationProgram.program_area_id == ProgramArea.id
    ).filter(
        OrganizationProgram.organization_id == organization.id,
        OrganizationProgram.is_active == True
    ).all()
    
    added_ids = [area.id for area in added_program_areas]
    
    return render_template('program_compliance/add_program_area.html',
                          organization=organization,
                          program_areas=program_areas,
                          added_ids=added_ids)

@program_compliance_bp.route('/program-areas/<int:program_id>/requirements')
@login_required
def program_requirements(program_id):
    """View requirements for a program area"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get organization program
    org_program = OrganizationProgram.query.get_or_404(program_id)
    
    # Check if program belongs to user's organization
    if org_program.organization_id != organization.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('program_compliance.program_areas'))
    
    # Get program area
    program_area = ProgramArea.query.get(org_program.program_area_id)
    
    # Get requirements
    requirements = SectorRequirement.query.filter_by(
        program_area_id=program_area.id
    ).all()
    
    return render_template('program_compliance/program_requirements.html',
                          organization=organization,
                          program_area=program_area,
                          requirements=requirements,
                          org_program=org_program)

@program_compliance_bp.route('/local-permits')
@login_required
def local_permits():
    """View local permits"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all permits
    permits = LocalPermit.query.filter_by(
        organization_id=organization.id
    ).order_by(LocalPermit.expiry_date).all()
    
    return render_template('program_compliance/local_permits.html',
                          organization=organization,
                          permits=permits)

@program_compliance_bp.route('/local-permits/new', methods=['GET', 'POST'])
@login_required
def new_local_permit():
    """Add new local permit"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'local_permit_management'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        permit_type = request.form.get('permit_type')
        permit_number = request.form.get('permit_number')
        issuing_authority = request.form.get('issuing_authority')
        issue_date_str = request.form.get('issue_date')
        expiry_date_str = request.form.get('expiry_date')
        jurisdiction = request.form.get('jurisdiction')
        status = request.form.get('status', 'active')
        
        # Parse dates
        issue_date = None
        if issue_date_str:
            try:
                issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid issue date format.', 'danger')
                return redirect(url_for('program_compliance.new_local_permit'))
        
        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid expiry date format.', 'danger')
                return redirect(url_for('program_compliance.new_local_permit'))
        
        # Handle file upload
        file_path = None
        if 'permit_file' in request.files:
            file = request.files['permit_file']
            if file and file.filename and allowed_file(file.filename, ['pdf', 'jpg', 'jpeg', 'png']):
                filename = secure_filename(file.filename)
                file_path = save_file(file, 'local_permits', filename)
        
        # Create permit
        permit = LocalPermit(
            organization_id=organization.id,
            permit_type=permit_type,
            permit_number=permit_number,
            issuing_authority=issuing_authority,
            issue_date=issue_date,
            expiry_date=expiry_date,
            jurisdiction=jurisdiction,
            status=status,
            file_path=file_path,
            created_by=current_user.id
        )
        
        db.session.add(permit)
        
        # Record feature usage
        record_feature_usage(organization.id, 'local_permit_management')
        
        db.session.commit()
        
        flash('Local permit added successfully.', 'success')
        return redirect(url_for('program_compliance.local_permits'))
    
    return render_template('program_compliance/new_local_permit.html',
                          organization=organization)

@program_compliance_bp.route('/compliance-risks')
@login_required
def compliance_risks():
    """View compliance risks"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all risks
    risks = ComplianceRisk.query.filter_by(
        organization_id=organization.id
    ).order_by(ComplianceRisk.risk_level.desc()).all()
    
    return render_template('program_compliance/compliance_risks.html',
                          organization=organization,
                          risks=risks)

@program_compliance_bp.route('/compliance-risks/new', methods=['GET', 'POST'])
@login_required
def new_compliance_risk():
    """Add new compliance risk"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'compliance_risk_assessment'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        program_area_id = request.form.get('program_area_id')
        likelihood = int(request.form.get('likelihood', 1))
        impact = int(request.form.get('impact', 1))
        mitigation_plan = request.form.get('mitigation_plan')
        status = request.form.get('status', 'identified')
        
        # Calculate risk level
        risk_score = likelihood * impact
        risk_level = 'low'
        if risk_score >= 15:
            risk_level = 'critical'
        elif risk_score >= 10:
            risk_level = 'high'
        elif risk_score >= 5:
            risk_level = 'medium'
        
        # Create risk
        risk = ComplianceRisk(
            organization_id=organization.id,
            program_area_id=program_area_id if program_area_id else None,
            title=title,
            description=description,
            likelihood=likelihood,
            impact=impact,
            risk_level=risk_level,
            mitigation_plan=mitigation_plan,
            status=status,
            created_by=current_user.id
        )
        
        db.session.add(risk)
        
        # Record feature usage
        record_feature_usage(organization.id, 'compliance_risk_assessment')
        
        db.session.commit()
        
        flash('Compliance risk added successfully.', 'success')
        return redirect(url_for('program_compliance.compliance_risks'))
    
    # Get organization's program areas
    program_areas = db.session.query(ProgramArea).join(
        OrganizationProgram, OrganizationProgram.program_area_id == ProgramArea.id
    ).filter(
        OrganizationProgram.organization_id == organization.id,
        OrganizationProgram.is_active == True
    ).all()
    
    return render_template('program_compliance/new_compliance_risk.html',
                          organization=organization,
                          program_areas=program_areas)

@program_compliance_bp.route('/compliance-risks/<int:risk_id>/update', methods=['GET', 'POST'])
@login_required
def update_compliance_risk(risk_id):
    """Update compliance risk"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get risk
    risk = ComplianceRisk.query.get_or_404(risk_id)
    
    # Check if risk belongs to user's organization
    if risk.organization_id != organization.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('program_compliance.compliance_risks'))
    
    if request.method == 'POST':
        mitigation_plan = request.form.get('mitigation_plan')
        status = request.form.get('status')
        
        # Update risk
        risk.mitigation_plan = mitigation_plan
        risk.status = status
        
        db.session.add(risk)
        db.session.commit()
        
        flash('Compliance risk updated successfully.', 'success')
        return redirect(url_for('program_compliance.compliance_risks'))
    
    return render_template('program_compliance/update_compliance_risk.html',
                          organization=organization,
                          risk=risk)

@program_compliance_bp.route('/sector-requirements')
@login_required
def sector_requirements():
    """View all sector requirements"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get organization's program areas
    program_areas = db.session.query(ProgramArea).join(
        OrganizationProgram, OrganizationProgram.program_area_id == ProgramArea.id
    ).filter(
        OrganizationProgram.organization_id == organization.id,
        OrganizationProgram.is_active == True
    ).all()
    
    # Get requirements for these program areas
    requirements = []
    for area in program_areas:
        area_requirements = SectorRequirement.query.filter_by(
            program_area_id=area.id
        ).all()
        requirements.extend(area_requirements)
    
    return render_template('program_compliance/sector_requirements.html',
                          organization=organization,
                          requirements=requirements,
                          program_areas=program_areas)

@program_compliance_bp.route('/compliance-report')
@login_required
def compliance_report():
    """Generate program compliance report"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'program_compliance_report'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Get program areas count
    program_areas_count = OrganizationProgram.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).count()
    
    # Get active permits count
    active_permits_count = LocalPermit.query.filter_by(
        organization_id=organization.id,
        status='active'
    ).count()
    
    # Get expired permits count
    expired_permits_count = LocalPermit.query.filter_by(
        organization_id=organization.id,
        status='expired'
    ).count()
    
    # Get risks by level
    critical_risks_count = ComplianceRisk.query.filter_by(
        organization_id=organization.id,
        risk_level='critical'
    ).count()
    
    high_risks_count = ComplianceRisk.query.filter_by(
        organization_id=organization.id,
        risk_level='high'
    ).count()
    
    medium_risks_count = ComplianceRisk.query.filter_by(
        organization_id=organization.id,
        risk_level='medium'
    ).count()
    
    low_risks_count = ComplianceRisk.query.filter_by(
        organization_id=organization.id,
        risk_level='low'
    ).count()
    
    # Get mitigated risks count
    mitigated_risks_count = ComplianceRisk.query.filter_by(
        organization_id=organization.id,
        status='mitigated'
    ).count()
    
    # Calculate compliance score
    compliance_score = calculate_program_compliance_score(organization.id)
    
    # Record feature usage
    record_feature_usage(organization.id, 'program_compliance_report')
    
    return render_template('program_compliance/compliance_report.html',
                          organization=organization,
                          program_areas_count=program_areas_count,
                          active_permits_count=active_permits_count,
                          expired_permits_count=expired_permits_count,
                          critical_risks_count=critical_risks_count,
                          high_risks_count=high_risks_count,
                          medium_risks_count=medium_risks_count,
                          low_risks_count=low_risks_count,
                          mitigated_risks_count=mitigated_risks_count,
                          compliance_score=compliance_score)

# Helper functions
def calculate_program_compliance_score(organization_id):
    """Calculate program compliance score (0-100)"""
    score = 0
    
    # Check program areas
    program_areas = OrganizationProgram.query.filter_by(
        organization_id=organization_id,
        is_active=True
    ).count()
    
    if program_areas > 0:
        score += 10  # Has defined program areas
    
    # Check local permits
    active_permits = LocalPermit.query.filter_by(
        organization_id=organization_id,
        status='active'
    ).count()
    
    expired_permits = LocalPermit.query.filter_by(
        organization_id=organization_id,
        status='expired'
    ).count()
    
    if active_permits > 0 and expired_permits == 0:
        score += 30  # All permits active
    elif active_permits > 0:
        score += 15  # Some permits active
    
    # Check compliance risks
    critical_risks = ComplianceRisk.query.filter_by(
        organization_id=organization_id,
        risk_level='critical',
        status='identified'
    ).count()
    
    high_risks = ComplianceRisk.query.filter_by(
        organization_id=organization_id,
        risk_level='high',
        status='identified'
    ).count()
    
    mitigated_risks = ComplianceRisk.query.filter_by(
        organization_id=organization_id,
        status='mitigated'
    ).count()
    
    if critical_risks == 0 and high_risks == 0:
        score += 30  # No critical or high risks
    elif critical_risks == 0:
        score += 20  # No critical risks
    elif high_risks == 0:
        score += 10  # No high risks
    
    if mitigated_risks > 0:
        score += 10  # Has mitigated risks
    
    # Check if has any risks identified (showing risk assessment activity)
    total_risks = ComplianceRisk.query.filter_by(
        organization_id=organization_id
    ).count()
    
    if total_risks > 0:
        score += 10  # Has conducted risk assessment
    
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
