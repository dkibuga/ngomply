from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, send_file
from flask_login import login_required, current_user
from app.models.models import ComplianceTask, Organization, AIGeneratedDocument, User
from app.forms.compliance_forms import ComplianceTaskForm
from app import db
from datetime import datetime, timedelta
from app.utils.email import send_notification_email

compliance_bp = Blueprint('compliance', __name__)

@compliance_bp.route('/')
@login_required
def index():
    """Compliance module home page"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get upcoming tasks
    upcoming_tasks = ComplianceTask.query.filter_by(
        organization_id=current_user.organization_id,
        completed=False
    ).order_by(ComplianceTask.due_date).limit(5).all()
    
    # Get overdue tasks
    overdue_tasks = ComplianceTask.query.filter(
        ComplianceTask.organization_id == current_user.organization_id,
        ComplianceTask.completed == False,
        ComplianceTask.due_date < datetime.utcnow()
    ).order_by(ComplianceTask.due_date).all()
    
    # Get recently completed tasks
    completed_tasks = ComplianceTask.query.filter_by(
        organization_id=current_user.organization_id,
        completed=True
    ).order_by(ComplianceTask.completion_date.desc()).limit(5).all()
    
    # Pass current time for date comparisons in template
    now = datetime.utcnow()
    
    return render_template('compliance/index.html', 
                          organization=organization,
                          upcoming_tasks=upcoming_tasks,
                          overdue_tasks=overdue_tasks,
                          completed_tasks=completed_tasks,
                          ComplianceTask=ComplianceTask,
                          now=now)

@compliance_bp.route('/tasks')
@login_required
def tasks():
    """List all compliance tasks"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    # Get filter parameters
    status = request.args.get('status', 'all')
    task_type = request.args.get('type', 'all')
    
    # Base query
    query = ComplianceTask.query.filter_by(organization_id=current_user.organization_id)
    
    # Apply filters
    if status == 'pending':
        query = query.filter_by(completed=False)
    elif status == 'completed':
        query = query.filter_by(completed=True)
    
    if task_type != 'all':
        query = query.filter_by(task_type=task_type)
    
    # Order by due date (pending) or completion date (completed)
    if status == 'completed':
        tasks = query.order_by(ComplianceTask.completion_date.desc()).all()
    else:
        tasks = query.order_by(ComplianceTask.due_date).all()
    
    # Pass current time for date comparisons in template
    now = datetime.utcnow()
    
    return render_template('compliance/tasks.html', 
                          tasks=tasks, 
                          status=status, 
                          task_type=task_type,
                          ComplianceTask=ComplianceTask,
                          now=now)

@compliance_bp.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    """Add a new compliance task"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    form = ComplianceTaskForm()
    if form.validate_on_submit():
        task = ComplianceTask(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            task_type=form.task_type.data,
            organization_id=current_user.organization_id,
            created_by=current_user.id
        )
        db.session.add(task)
        db.session.commit()
        
        flash('Task added successfully!', 'success')
        return redirect(url_for('compliance.tasks'))
    
    return render_template('compliance/add_task.html', form=form)

@compliance_bp.route('/task/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    """Mark a task as complete"""
    task = ComplianceTask.query.get_or_404(task_id)
    
    # Check if user has permission to update this task
    if task.organization_id != current_user.organization_id and not current_user.role == 'admin':
        abort(403)
    
    task.completed = True
    task.completion_date = datetime.utcnow()
    task.completed_by = current_user.id
    db.session.commit()
    
    flash('Task marked as complete!', 'success')
    return redirect(url_for('compliance.tasks'))

@compliance_bp.route('/task/<int:task_id>/reopen', methods=['POST'])
@login_required
def reopen_task(task_id):
    """Reopen a completed task"""
    task = ComplianceTask.query.get_or_404(task_id)
    
    # Check if user has permission to update this task
    if task.organization_id != current_user.organization_id and not current_user.role == 'admin':
        abort(403)
    
    task.completed = False
    task.completion_date = None
    task.completed_by = None
    db.session.commit()
    
    flash('Task reopened!', 'success')
    return redirect(url_for('compliance.tasks'))

@compliance_bp.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    """Delete a task"""
    task = ComplianceTask.query.get_or_404(task_id)
    
    # Check if user has permission to delete this task
    if task.organization_id != current_user.organization_id and not current_user.role == 'admin':
        abort(403)
    
    db.session.delete(task)
    db.session.commit()
    
    flash('Task deleted!', 'success')
    return redirect(url_for('compliance.tasks'))

@compliance_bp.route('/audit_support')
@login_required
def audit_support():
    """Audit support page"""
    # Check if user has an organization
    organization = None
    if current_user.organization_id:
        organization = Organization.query.get(current_user.organization_id)
    
    # Get previously generated audit methodologies
    methodologies = AIGeneratedDocument.query.filter_by(
        user_id=current_user.id,
        document_type='Audit Methodology'
    ).order_by(AIGeneratedDocument.created_at.desc()).all()
    
    return render_template('compliance/audit_support.html', 
                          organization=organization,
                          methodologies=methodologies)

@compliance_bp.route('/send_reminders')
@login_required
def send_reminders():
    """Send reminders for upcoming tasks"""
    # Check if user has an organization and is admin/staff
    if not current_user.organization_id or current_user.role not in ['admin', 'staff']:
        flash('You do not have permission to send reminders.', 'warning')
        return redirect(url_for('compliance.index'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get upcoming tasks due in the next 7 days
    upcoming_tasks = ComplianceTask.query.filter(
        ComplianceTask.organization_id == current_user.organization_id,
        ComplianceTask.completed == False,
        ComplianceTask.due_date <= datetime.utcnow() + timedelta(days=7),
        ComplianceTask.due_date >= datetime.utcnow()
    ).order_by(ComplianceTask.due_date).all()
    
    # Get users in the organization
    users = User.query.filter_by(organization_id=current_user.organization_id).all()
    
    # Send reminders
    for user in users:
        if upcoming_tasks:
            task_list = "\n".join([f"- {task.title} (Due: {task.due_date.strftime('%Y-%m-%d')})" for task in upcoming_tasks])
            message = f"You have {len(upcoming_tasks)} upcoming compliance tasks:\n\n{task_list}\n\nPlease log in to NGOmply to complete these tasks."
            send_notification_email(user, "Upcoming Compliance Tasks", message)
    
    flash(f'Reminders sent to {len(users)} users about {len(upcoming_tasks)} upcoming tasks.', 'success')
    return redirect(url_for('compliance.index'))
