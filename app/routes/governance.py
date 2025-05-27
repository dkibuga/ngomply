from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app.models.governance_models import BoardMeeting, BoardMember, ConflictOfInterest, GovernancePolicy, BoardEvaluation
from app.models.models import Organization, User, Document
from app.models.subscription_models import Subscription, Feature, UsageRecord, TierFeature
from app import db
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from app.utils.file_handlers import allowed_file, save_file

governance_bp = Blueprint('governance', __name__)

@governance_bp.route('/')
@login_required
def index():
    """Board Governance Module home page"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get board members
    board_members = BoardMember.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).all()
    
    # Get upcoming meetings
    upcoming_meetings = BoardMeeting.query.filter(
        BoardMeeting.organization_id == organization.id,
        BoardMeeting.meeting_date >= datetime.utcnow(),
        BoardMeeting.status == 'scheduled'
    ).order_by(BoardMeeting.meeting_date).limit(3).all()
    
    # Get recent meetings
    recent_meetings = BoardMeeting.query.filter(
        BoardMeeting.organization_id == organization.id,
        BoardMeeting.meeting_date < datetime.utcnow(),
        BoardMeeting.status == 'completed'
    ).order_by(BoardMeeting.meeting_date.desc()).limit(3).all()
    
    # Get governance policies
    policies = GovernancePolicy.query.filter_by(
        organization_id=organization.id,
        status='approved'
    ).order_by(GovernancePolicy.approval_date.desc()).all()
    
    # Calculate governance score
    governance_score = calculate_governance_score(organization.id)
    
    return render_template('governance/index.html',
                          organization=organization,
                          board_members=board_members,
                          upcoming_meetings=upcoming_meetings,
                          recent_meetings=recent_meetings,
                          policies=policies,
                          governance_score=governance_score)

@governance_bp.route('/board-members')
@login_required
def board_members():
    """View board members"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all board members
    members = BoardMember.query.filter_by(
        organization_id=organization.id
    ).order_by(BoardMember.start_date.desc()).all()
    
    return render_template('governance/board_members.html',
                          organization=organization,
                          members=members)

@governance_bp.route('/board-members/new', methods=['GET', 'POST'])
@login_required
def new_board_member():
    """Add new board member"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'board_management'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        position = request.form.get('position')
        email = request.form.get('email')
        phone = request.form.get('phone')
        bio = request.form.get('bio')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        is_active = request.form.get('is_active') == 'on'
        
        # Parse dates
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid start date format.', 'danger')
                return redirect(url_for('governance.new_board_member'))
        
        end_date = None
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid end date format.', 'danger')
                return redirect(url_for('governance.new_board_member'))
        
        # Create board member
        member = BoardMember(
            organization_id=organization.id,
            name=name,
            position=position,
            email=email,
            phone=phone,
            bio=bio,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active
        )
        
        db.session.add(member)
        
        # Record feature usage
        record_feature_usage(organization.id, 'board_management')
        
        db.session.commit()
        
        flash('Board member added successfully.', 'success')
        return redirect(url_for('governance.board_members'))
    
    return render_template('governance/new_board_member.html',
                          organization=organization)

@governance_bp.route('/board-meetings')
@login_required
def board_meetings():
    """View board meetings"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all meetings
    meetings = BoardMeeting.query.filter_by(
        organization_id=organization.id
    ).order_by(BoardMeeting.meeting_date.desc()).all()
    
    return render_template('governance/board_meetings.html',
                          organization=organization,
                          meetings=meetings)

@governance_bp.route('/board-meetings/new', methods=['GET', 'POST'])
@login_required
def new_board_meeting():
    """Schedule new board meeting"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'board_meeting_management'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        meeting_date_str = request.form.get('meeting_date')
        location = request.form.get('location')
        attendees = request.form.get('attendees')
        agenda = request.form.get('agenda')
        status = request.form.get('status', 'scheduled')
        
        # Parse date
        meeting_date = None
        if meeting_date_str:
            try:
                meeting_date = datetime.strptime(meeting_date_str, '%Y-%m-%d %H:%M')
            except ValueError:
                flash('Invalid meeting date format.', 'danger')
                return redirect(url_for('governance.new_board_meeting'))
        
        # Create board meeting
        meeting = BoardMeeting(
            organization_id=organization.id,
            title=title,
            meeting_date=meeting_date,
            location=location,
            attendees=attendees,
            agenda=agenda,
            status=status,
            created_by=current_user.id
        )
        
        db.session.add(meeting)
        
        # Record feature usage
        record_feature_usage(organization.id, 'board_meeting_management')
        
        db.session.commit()
        
        flash('Board meeting scheduled successfully.', 'success')
        return redirect(url_for('governance.board_meetings'))
    
    # Get board members for attendees list
    board_members = BoardMember.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).all()
    
    return render_template('governance/new_board_meeting.html',
                          organization=organization,
                          board_members=board_members)

@governance_bp.route('/board-meetings/<int:meeting_id>')
@login_required
def view_board_meeting(meeting_id):
    """View board meeting details"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get meeting
    meeting = BoardMeeting.query.get_or_404(meeting_id)
    
    # Check if meeting belongs to user's organization
    if meeting.organization_id != organization.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('governance.board_meetings'))
    
    return render_template('governance/view_board_meeting.html',
                          organization=organization,
                          meeting=meeting)

@governance_bp.route('/board-meetings/<int:meeting_id>/minutes', methods=['GET', 'POST'])
@login_required
def add_minutes(meeting_id):
    """Add minutes to a board meeting"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get meeting
    meeting = BoardMeeting.query.get_or_404(meeting_id)
    
    # Check if meeting belongs to user's organization
    if meeting.organization_id != organization.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('governance.board_meetings'))
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'board_meeting_minutes'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        minutes = request.form.get('minutes')
        resolutions = request.form.get('resolutions')
        minutes_approved = request.form.get('minutes_approved') == 'on'
        
        # Handle file upload
        file_path = None
        if 'minutes_file' in request.files:
            file = request.files['minutes_file']
            if file and file.filename and allowed_file(file.filename, ['pdf', 'docx']):
                filename = secure_filename(file.filename)
                file_path = save_file(file, 'board_minutes', filename)
        
        # Update meeting
        meeting.minutes = minutes
        meeting.resolutions = resolutions
        meeting.minutes_approved = minutes_approved
        
        if minutes_approved:
            meeting.minutes_approval_date = datetime.utcnow()
        
        if file_path:
            meeting.file_path = file_path
        
        if meeting.status == 'scheduled':
            meeting.status = 'completed'
        
        db.session.add(meeting)
        
        # Record feature usage
        record_feature_usage(organization.id, 'board_meeting_minutes')
        
        db.session.commit()
        
        flash('Meeting minutes added successfully.', 'success')
        return redirect(url_for('governance.view_board_meeting', meeting_id=meeting.id))
    
    return render_template('governance/add_minutes.html',
                          organization=organization,
                          meeting=meeting)

@governance_bp.route('/conflict-of-interest')
@login_required
def conflict_of_interest():
    """View conflict of interest declarations"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all declarations
    declarations = ConflictOfInterest.query.filter_by(
        organization_id=organization.id
    ).order_by(ConflictOfInterest.declaration_date.desc()).all()
    
    return render_template('governance/conflict_of_interest.html',
                          organization=organization,
                          declarations=declarations)

@governance_bp.route('/conflict-of-interest/new', methods=['GET', 'POST'])
@login_required
def new_conflict_declaration():
    """Create new conflict of interest declaration"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'conflict_of_interest_management'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        board_member_id = request.form.get('board_member_id')
        description = request.form.get('description')
        nature = request.form.get('nature')
        declaration_date_str = request.form.get('declaration_date')
        resolution = request.form.get('resolution')
        status = request.form.get('status', 'declared')
        
        # Parse date
        declaration_date = None
        if declaration_date_str:
            try:
                declaration_date = datetime.strptime(declaration_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid declaration date format.', 'danger')
                return redirect(url_for('governance.new_conflict_declaration'))
        
        # Handle file upload
        file_path = None
        if 'declaration_file' in request.files:
            file = request.files['declaration_file']
            if file and file.filename and allowed_file(file.filename, ['pdf', 'docx']):
                filename = secure_filename(file.filename)
                file_path = save_file(file, 'conflict_declarations', filename)
        
        # Create declaration
        declaration = ConflictOfInterest(
            board_member_id=board_member_id,
            organization_id=organization.id,
            description=description,
            nature=nature,
            declaration_date=declaration_date,
            resolution=resolution,
            status=status,
            file_path=file_path
        )
        
        db.session.add(declaration)
        
        # Record feature usage
        record_feature_usage(organization.id, 'conflict_of_interest_management')
        
        db.session.commit()
        
        flash('Conflict of interest declaration created successfully.', 'success')
        return redirect(url_for('governance.conflict_of_interest'))
    
    # Get board members
    board_members = BoardMember.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).all()
    
    return render_template('governance/new_conflict_declaration.html',
                          organization=organization,
                          board_members=board_members)

@governance_bp.route('/policies')
@login_required
def policies():
    """View governance policies"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all policies
    policies = GovernancePolicy.query.filter_by(
        organization_id=organization.id
    ).order_by(GovernancePolicy.created_at.desc()).all()
    
    return render_template('governance/policies.html',
                          organization=organization,
                          policies=policies)

@governance_bp.route('/policies/new', methods=['GET', 'POST'])
@login_required
def new_policy():
    """Create new governance policy"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'governance_policy_management'):
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
                return redirect(url_for('governance.new_policy'))
        
        review_date = None
        if review_date_str:
            try:
                review_date = datetime.strptime(review_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid review date format.', 'danger')
                return redirect(url_for('governance.new_policy'))
        
        # Handle file upload
        file_path = None
        if 'policy_file' in request.files:
            file = request.files['policy_file']
            if file and file.filename and allowed_file(file.filename, ['pdf', 'docx']):
                filename = secure_filename(file.filename)
                file_path = save_file(file, 'governance_policies', filename)
        
        # Create policy
        policy = GovernancePolicy(
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
        record_feature_usage(organization.id, 'governance_policy_management')
        
        db.session.commit()
        
        flash('Governance policy created successfully.', 'success')
        return redirect(url_for('governance.policies'))
    
    return render_template('governance/new_policy.html',
                          organization=organization)

@governance_bp.route('/board-evaluations')
@login_required
def board_evaluations():
    """View board evaluations"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all evaluations
    evaluations = BoardEvaluation.query.filter_by(
        organization_id=organization.id
    ).order_by(BoardEvaluation.evaluation_date.desc()).all()
    
    return render_template('governance/board_evaluations.html',
                          organization=organization,
                          evaluations=evaluations)

@governance_bp.route('/board-evaluations/new', methods=['GET', 'POST'])
@login_required
def new_board_evaluation():
    """Create new board evaluation"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'board_evaluation'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        evaluation_date_str = request.form.get('evaluation_date')
        evaluation_period = request.form.get('evaluation_period')
        methodology = request.form.get('methodology')
        strengths = request.form.get('strengths')
        weaknesses = request.form.get('weaknesses')
        recommendations = request.form.get('recommendations')
        action_plan = request.form.get('action_plan')
        status = request.form.get('status', 'planned')
        
        # Parse date
        evaluation_date = None
        if evaluation_date_str:
            try:
                evaluation_date = datetime.strptime(evaluation_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid evaluation date format.', 'danger')
                return redirect(url_for('governance.new_board_evaluation'))
        
        # Handle file upload
        file_path = None
        if 'evaluation_file' in request.files:
            file = request.files['evaluation_file']
            if file and file.filename and allowed_file(file.filename, ['pdf', 'docx']):
                filename = secure_filename(file.filename)
                file_path = save_file(file, 'board_evaluations', filename)
        
        # Create evaluation
        evaluation = BoardEvaluation(
            organization_id=organization.id,
            title=title,
            evaluation_date=evaluation_date,
            evaluation_period=evaluation_period,
            methodology=methodology,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            action_plan=action_plan,
            status=status,
            file_path=file_path,
            created_by=current_user.id
        )
        
        db.session.add(evaluation)
        
        # Record feature usage
        record_feature_usage(organization.id, 'board_evaluation')
        
        db.session.commit()
        
        flash('Board evaluation created successfully.', 'success')
        return redirect(url_for('governance.board_evaluations'))
    
    return render_template('governance/new_board_evaluation.html',
                          organization=organization)

@governance_bp.route('/compliance-report')
@login_required
def compliance_report():
    """Generate governance compliance report"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'governance_compliance_report'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Get board members count
    board_members_count = BoardMember.query.filter_by(
        organization_id=organization.id,
        is_active=True
    ).count()
    
    # Get meetings count
    meetings_count = BoardMeeting.query.filter(
        BoardMeeting.organization_id == organization.id,
        BoardMeeting.meeting_date >= datetime.utcnow() - timedelta(days=365)
    ).count()
    
    # Get policies count
    policies_count = GovernancePolicy.query.filter_by(
        organization_id=organization.id,
        status='approved'
    ).count()
    
    # Get conflict declarations count
    conflicts_count = ConflictOfInterest.query.filter_by(
        organization_id=organization.id
    ).count()
    
    # Get evaluations count
    evaluations_count = BoardEvaluation.query.filter_by(
        organization_id=organization.id,
        status='completed'
    ).count()
    
    # Calculate governance score
    governance_score = calculate_governance_score(organization.id)
    
    # Record feature usage
    record_feature_usage(organization.id, 'governance_compliance_report')
    
    return render_template('governance/compliance_report.html',
                          organization=organization,
                          board_members_count=board_members_count,
                          meetings_count=meetings_count,
                          policies_count=policies_count,
                          conflicts_count=conflicts_count,
                          evaluations_count=evaluations_count,
                          governance_score=governance_score)

# Helper functions
def calculate_governance_score(organization_id):
    """Calculate governance compliance score (0-100)"""
    score = 0
    
    # Check board composition
    board_members = BoardMember.query.filter_by(
        organization_id=organization_id,
        is_active=True
    ).count()
    
    if board_members >= 5:  # Good board size
        score += 20
    elif board_members >= 3:  # Minimum board size
        score += 10
    
    # Check board meetings
    meetings_last_year = BoardMeeting.query.filter(
        BoardMeeting.organization_id == organization_id,
        BoardMeeting.meeting_date >= datetime.utcnow() - timedelta(days=365),
        BoardMeeting.status == 'completed'
    ).count()
    
    if meetings_last_year >= 4:  # Quarterly meetings
        score += 20
    elif meetings_last_year >= 2:  # Semi-annual meetings
        score += 10
    
    # Check governance policies
    policies = GovernancePolicy.query.filter_by(
        organization_id=organization_id,
        status='approved'
    ).count()
    
    if policies >= 3:  # Multiple policies
        score += 20
    elif policies >= 1:  # At least one policy
        score += 10
    
    # Check conflict of interest management
    conflicts = ConflictOfInterest.query.filter_by(
        organization_id=organization_id
    ).count()
    
    if conflicts > 0:  # Has conflict declarations
        score += 20
    
    # Check board evaluations
    evaluations = BoardEvaluation.query.filter_by(
        organization_id=organization_id,
        status='completed'
    ).count()
    
    if evaluations > 0:  # Has completed evaluations
        score += 20
    
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
