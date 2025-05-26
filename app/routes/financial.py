from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app.models.financial_models import FinancialReport, BudgetItem, TaxExemption, AuditFinding, FinancialPolicy
from app.models.models import Organization, User, Document
from app.models.subscription_models import Subscription, Feature, UsageRecord
from app import db
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from app.utils.file_handlers import allowed_file, save_file

financial_bp = Blueprint('financial', __name__)

@financial_bp.route('/')
@login_required
def index():
    """Financial Compliance Module home page"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get recent financial reports
    reports = FinancialReport.query.filter_by(
        organization_id=organization.id
    ).order_by(FinancialReport.created_at.desc()).limit(5).all()
    
    # Get tax exemptions
    exemptions = TaxExemption.query.filter_by(
        organization_id=organization.id,
        status='active'
    ).all()
    
    # Get financial policies
    policies = FinancialPolicy.query.filter_by(
        organization_id=organization.id,
        status='approved'
    ).order_by(FinancialPolicy.approval_date.desc()).all()
    
    # Calculate compliance score
    compliance_score = calculate_financial_compliance_score(organization.id)
    
    return render_template('financial/index.html',
                          organization=organization,
                          reports=reports,
                          exemptions=exemptions,
                          policies=policies,
                          compliance_score=compliance_score)

@financial_bp.route('/reports')
@login_required
def reports():
    """View financial reports"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all reports
    reports = FinancialReport.query.filter_by(
        organization_id=organization.id
    ).order_by(FinancialReport.created_at.desc()).all()
    
    return render_template('financial/reports.html',
                          organization=organization,
                          reports=reports)

@financial_bp.route('/reports/new', methods=['GET', 'POST'])
@login_required
def new_report():
    """Create new financial report"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'financial_reporting'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        report_type = request.form.get('report_type')
        fiscal_year = request.form.get('fiscal_year')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        status = request.form.get('status', 'draft')
        submission_date_str = request.form.get('submission_date')
        submitted_to = request.form.get('submitted_to')
        
        # Parse dates
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid start date format.', 'danger')
                return redirect(url_for('financial.new_report'))
        
        end_date = None
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid end date format.', 'danger')
                return redirect(url_for('financial.new_report'))
        
        submission_date = None
        if submission_date_str:
            try:
                submission_date = datetime.strptime(submission_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid submission date format.', 'danger')
                return redirect(url_for('financial.new_report'))
        
        # Handle file upload
        file_path = None
        if 'report_file' in request.files:
            file = request.files['report_file']
            if file and file.filename and allowed_file(file.filename, ['pdf', 'xlsx', 'docx']):
                filename = secure_filename(file.filename)
                file_path = save_file(file, 'financial_reports', filename)
        
        # Create report
        report = FinancialReport(
            organization_id=organization.id,
            title=title,
            report_type=report_type,
            fiscal_year=fiscal_year,
            start_date=start_date,
            end_date=end_date,
            file_path=file_path,
            status=status,
            submission_date=submission_date,
            submitted_to=submitted_to,
            created_by=current_user.id
        )
        
        db.session.add(report)
        
        # Record feature usage
        record_feature_usage(organization.id, 'financial_reporting')
        
        db.session.commit()
        
        flash('Financial report created successfully.', 'success')
        return redirect(url_for('financial.reports'))
    
    return render_template('financial/new_report.html',
                          organization=organization)

@financial_bp.route('/reports/<int:report_id>')
@login_required
def view_report(report_id):
    """View a financial report"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get report
    report = FinancialReport.query.get_or_404(report_id)
    
    # Check if report belongs to user's organization
    if report.organization_id != organization.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('financial.reports'))
    
    # Get budget items if any
    budget_items = BudgetItem.query.filter_by(report_id=report.id).all()
    
    # Get audit findings if any
    audit_findings = AuditFinding.query.filter_by(report_id=report.id).all()
    
    return render_template('financial/view_report.html',
                          organization=organization,
                          report=report,
                          budget_items=budget_items,
                          audit_findings=audit_findings)

@financial_bp.route('/reports/<int:report_id>/budget', methods=['GET', 'POST'])
@login_required
def manage_budget(report_id):
    """Manage budget items for a report"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get report
    report = FinancialReport.query.get_or_404(report_id)
    
    # Check if report belongs to user's organization
    if report.organization_id != organization.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('financial.reports'))
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'budget_management'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        # Add new budget item
        category = request.form.get('category')
        description = request.form.get('description')
        amount_budgeted = request.form.get('amount_budgeted')
        amount_actual = request.form.get('amount_actual')
        variance_explanation = request.form.get('variance_explanation')
        
        # Calculate variance
        variance = 0
        if amount_actual and amount_budgeted:
            variance = float(amount_actual) - float(amount_budgeted)
        
        # Create budget item
        budget_item = BudgetItem(
            report_id=report.id,
            category=category,
            description=description,
            amount_budgeted=float(amount_budgeted),
            amount_actual=float(amount_actual) if amount_actual else None,
            variance=variance,
            variance_explanation=variance_explanation
        )
        
        db.session.add(budget_item)
        
        # Record feature usage
        record_feature_usage(organization.id, 'budget_management')
        
        db.session.commit()
        
        flash('Budget item added successfully.', 'success')
        return redirect(url_for('financial.manage_budget', report_id=report.id))
    
    # Get existing budget items
    budget_items = BudgetItem.query.filter_by(report_id=report.id).all()
    
    return render_template('financial/manage_budget.html',
                          organization=organization,
                          report=report,
                          budget_items=budget_items)

@financial_bp.route('/tax-exemptions')
@login_required
def tax_exemptions():
    """View tax exemptions"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all tax exemptions
    exemptions = TaxExemption.query.filter_by(
        organization_id=organization.id
    ).order_by(TaxExemption.created_at.desc()).all()
    
    return render_template('financial/tax_exemptions.html',
                          organization=organization,
                          exemptions=exemptions)

@financial_bp.route('/tax-exemptions/new', methods=['GET', 'POST'])
@login_required
def new_tax_exemption():
    """Create new tax exemption"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'tax_exemption_management'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        certificate_number = request.form.get('certificate_number')
        issue_date_str = request.form.get('issue_date')
        expiry_date_str = request.form.get('expiry_date')
        tax_type = request.form.get('tax_type')
        issuing_authority = request.form.get('issuing_authority')
        status = request.form.get('status', 'active')
        
        # Parse dates
        issue_date = None
        if issue_date_str:
            try:
                issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid issue date format.', 'danger')
                return redirect(url_for('financial.new_tax_exemption'))
        
        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid expiry date format.', 'danger')
                return redirect(url_for('financial.new_tax_exemption'))
        
        # Handle file upload
        file_path = None
        if 'certificate_file' in request.files:
            file = request.files['certificate_file']
            if file and file.filename and allowed_file(file.filename, ['pdf', 'jpg', 'jpeg', 'png']):
                filename = secure_filename(file.filename)
                file_path = save_file(file, 'tax_exemptions', filename)
        
        # Create tax exemption
        exemption = TaxExemption(
            organization_id=organization.id,
            certificate_number=certificate_number,
            issue_date=issue_date,
            expiry_date=expiry_date,
            tax_type=tax_type,
            issuing_authority=issuing_authority,
            file_path=file_path,
            status=status,
            created_by=current_user.id
        )
        
        db.session.add(exemption)
        
        # Record feature usage
        record_feature_usage(organization.id, 'tax_exemption_management')
        
        db.session.commit()
        
        flash('Tax exemption created successfully.', 'success')
        return redirect(url_for('financial.tax_exemptions'))
    
    return render_template('financial/new_tax_exemption.html',
                          organization=organization)

@financial_bp.route('/audit-findings')
@login_required
def audit_findings():
    """View audit findings"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all audit findings for organization's reports
    findings = db.session.query(AuditFinding).join(
        FinancialReport, AuditFinding.report_id == FinancialReport.id
    ).filter(
        FinancialReport.organization_id == organization.id
    ).order_by(AuditFinding.created_at.desc()).all()
    
    return render_template('financial/audit_findings.html',
                          organization=organization,
                          findings=findings)

@financial_bp.route('/reports/<int:report_id>/audit-findings/new', methods=['GET', 'POST'])
@login_required
def new_audit_finding(report_id):
    """Create new audit finding for a report"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get report
    report = FinancialReport.query.get_or_404(report_id)
    
    # Check if report belongs to user's organization
    if report.organization_id != organization.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('financial.reports'))
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'audit_management'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        finding_type = request.form.get('finding_type')
        description = request.form.get('description')
        recommendation = request.form.get('recommendation')
        management_response = request.form.get('management_response')
        action_plan = request.form.get('action_plan')
        due_date_str = request.form.get('due_date')
        status = request.form.get('status', 'open')
        
        # Parse date
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid due date format.', 'danger')
                return redirect(url_for('financial.new_audit_finding', report_id=report.id))
        
        # Create audit finding
        finding = AuditFinding(
            report_id=report.id,
            finding_type=finding_type,
            description=description,
            recommendation=recommendation,
            management_response=management_response,
            action_plan=action_plan,
            due_date=due_date,
            status=status
        )
        
        db.session.add(finding)
        
        # Record feature usage
        record_feature_usage(organization.id, 'audit_management')
        
        db.session.commit()
        
        flash('Audit finding created successfully.', 'success')
        return redirect(url_for('financial.view_report', report_id=report.id))
    
    return render_template('financial/new_audit_finding.html',
                          organization=organization,
                          report=report)

@financial_bp.route('/policies')
@login_required
def policies():
    """View financial policies"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all policies
    policies = FinancialPolicy.query.filter_by(
        organization_id=organization.id
    ).order_by(FinancialPolicy.created_at.desc()).all()
    
    return render_template('financial/policies.html',
                          organization=organization,
                          policies=policies)

@financial_bp.route('/policies/new', methods=['GET', 'POST'])
@login_required
def new_policy():
    """Create new financial policy"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'financial_policy_management'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        policy_type = request.form.get('policy_type')
        content = request.form.get('content')
        version = request.form.get('version')
        approval_date_str = request.form.get('approval_date')
        review_date_str = request.form.get('review_date')
        status = request.form.get('status', 'draft')
        approved_by = request.form.get('approved_by')
        
        # Parse dates
        approval_date = None
        if approval_date_str:
            try:
                approval_date = datetime.strptime(approval_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid approval date format.', 'danger')
                return redirect(url_for('financial.new_policy'))
        
        review_date = None
        if review_date_str:
            try:
                review_date = datetime.strptime(review_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid review date format.', 'danger')
                return redirect(url_for('financial.new_policy'))
        
        # Handle file upload
        file_path = None
        if 'policy_file' in request.files:
            file = request.files['policy_file']
            if file and file.filename and allowed_file(file.filename, ['pdf', 'docx']):
                filename = secure_filename(file.filename)
                file_path = save_file(file, 'financial_policies', filename)
        
        # Create policy
        policy = FinancialPolicy(
            organization_id=organization.id,
            title=title,
            policy_type=policy_type,
            content=content,
            version=version,
            approval_date=approval_date,
            review_date=review_date,
            status=status,
            approved_by=approved_by,
            file_path=file_path,
            created_by=current_user.id
        )
        
        db.session.add(policy)
        
        # Record feature usage
        record_feature_usage(organization.id, 'financial_policy_management')
        
        db.session.commit()
        
        flash('Financial policy created successfully.', 'success')
        return redirect(url_for('financial.policies'))
    
    return render_template('financial/new_policy.html',
                          organization=organization)

@financial_bp.route('/annual-returns')
@login_required
def annual_returns():
    """View and manage annual returns"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get annual return reports
    annual_returns = FinancialReport.query.filter_by(
        organization_id=organization.id,
        report_type='annual_return'
    ).order_by(FinancialReport.created_at.desc()).all()
    
    return render_template('financial/annual_returns.html',
                          organization=organization,
                          annual_returns=annual_returns)

@financial_bp.route('/annual-returns/new', methods=['GET', 'POST'])
@login_required
def new_annual_return():
    """Create new annual return"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'annual_return_generation'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        fiscal_year = request.form.get('fiscal_year')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        status = request.form.get('status', 'draft')
        submission_date_str = request.form.get('submission_date')
        
        # Parse dates
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid start date format.', 'danger')
                return redirect(url_for('financial.new_annual_return'))
        
        end_date = None
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid end date format.', 'danger')
                return redirect(url_for('financial.new_annual_return'))
        
        submission_date = None
        if submission_date_str:
            try:
                submission_date = datetime.strptime(submission_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid submission date format.', 'danger')
                return redirect(url_for('financial.new_annual_return'))
        
        # Handle file upload
        file_path = None
        if 'return_file' in request.files:
            file = request.files['return_file']
            if file and file.filename and allowed_file(file.filename, ['pdf', 'xlsx', 'docx']):
                filename = secure_filename(file.filename)
                file_path = save_file(file, 'annual_returns', filename)
        
        # Create annual return report
        title = f"Annual Return - {fiscal_year}"
        report = FinancialReport(
            organization_id=organization.id,
            title=title,
            report_type='annual_return',
            fiscal_year=fiscal_year,
            start_date=start_date,
            end_date=end_date,
            file_path=file_path,
            status=status,
            submission_date=submission_date,
            submitted_to='NGO Bureau',
            created_by=current_user.id
        )
        
        db.session.add(report)
        
        # Record feature usage
        record_feature_usage(organization.id, 'annual_return_generation')
        
        db.session.commit()
        
        flash('Annual return created successfully.', 'success')
        return redirect(url_for('financial.annual_returns'))
    
    return render_template('financial/new_annual_return.html',
                          organization=organization)

@financial_bp.route('/compliance-report')
@login_required
def compliance_report():
    """Generate financial compliance report"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'financial_compliance_report'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Get annual returns count
    annual_returns_count = FinancialReport.query.filter_by(
        organization_id=organization.id,
        report_type='annual_return'
    ).count()
    
    # Get tax exemptions count
    tax_exemptions_count = TaxExemption.query.filter_by(
        organization_id=organization.id,
        status='active'
    ).count()
    
    # Get financial policies count
    policies_count = FinancialPolicy.query.filter_by(
        organization_id=organization.id,
        status='approved'
    ).count()
    
    # Get audit findings
    open_findings_count = db.session.query(AuditFinding).join(
        FinancialReport, AuditFinding.report_id == FinancialReport.id
    ).filter(
        FinancialReport.organization_id == organization.id,
        AuditFinding.status == 'open'
    ).count()
    
    resolved_findings_count = db.session.query(AuditFinding).join(
        FinancialReport, AuditFinding.report_id == FinancialReport.id
    ).filter(
        FinancialReport.organization_id == organization.id,
        AuditFinding.status == 'resolved'
    ).count()
    
    # Calculate compliance score
    compliance_score = calculate_financial_compliance_score(organization.id)
    
    # Record feature usage
    record_feature_usage(organization.id, 'financial_compliance_report')
    
    return render_template('financial/compliance_report.html',
                          organization=organization,
                          annual_returns_count=annual_returns_count,
                          tax_exemptions_count=tax_exemptions_count,
                          policies_count=policies_count,
                          open_findings_count=open_findings_count,
                          resolved_findings_count=resolved_findings_count,
                          compliance_score=compliance_score)

# Helper functions
def calculate_financial_compliance_score(organization_id):
    """Calculate financial compliance score (0-100)"""
    score = 0
    
    # Check annual returns
    current_year = datetime.utcnow().year
    last_year = current_year - 1
    
    annual_return = FinancialReport.query.filter(
        FinancialReport.organization_id == organization_id,
        FinancialReport.report_type == 'annual_return',
        FinancialReport.fiscal_year.like(f"%{last_year}%")
    ).first()
    
    if annual_return:
        if annual_return.status == 'submitted':
            score += 30
        elif annual_return.status == 'final':
            score += 20
        elif annual_return.status == 'draft':
            score += 10
    
    # Check tax exemptions
    exemptions = TaxExemption.query.filter_by(
        organization_id=organization_id,
        status='active'
    ).count()
    
    if exemptions > 0:
        score += 20
    
    # Check financial policies
    policies = FinancialPolicy.query.filter_by(
        organization_id=organization_id,
        status='approved'
    ).count()
    
    if policies >= 3:  # Has multiple policies
        score += 20
    elif policies > 0:  # Has at least one policy
        score += 10
    
    # Check audit findings
    open_findings = db.session.query(AuditFinding).join(
        FinancialReport, AuditFinding.report_id == FinancialReport.id
    ).filter(
        FinancialReport.organization_id == organization_id,
        AuditFinding.status == 'open'
    ).count()
    
    if open_findings == 0:
        score += 30
    elif open_findings <= 3:
        score += 15
    else:
        score += 5
    
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
