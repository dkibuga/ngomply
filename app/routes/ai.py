from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, abort
from flask_login import login_required, current_user
from app.models.models import AIGeneratedDocument, Organization
from app import db
from app.ai_agents.agents import DocumentGenerationAgent, AuditMethodologyAgent
import os
from datetime import datetime
from app.utils.file_handlers import save_file
import io

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/generate_document', methods=['POST'])
@login_required
def generate_document():
    """Generate a document using AI"""
    try:
        document_type = request.form.get('document_type')
        organization_id = request.form.get('organization_id')
        
        # Validate inputs
        if not document_type:
            flash('Document type is required', 'danger')
            return redirect(url_for('registration.ai_document_generation'))
        
        # Initialize AI agent
        doc_agent = DocumentGenerationAgent()
        
        # Get organization if provided
        organization = None
        if organization_id:
            organization = Organization.query.get(organization_id)
        
        # Generate document based on type
        content = ""
        title = ""
        
        if document_type == 'constitution':
            org_name = request.form.get('org_name') or (organization.name if organization else "")
            org_vision = request.form.get('org_vision', "")
            org_mission = request.form.get('org_mission', "")
            primary_objective = request.form.get('primary_objective', "")
            
            content = doc_agent.generate_constitution(
                org_name=org_name,
                org_vision=org_vision,
                org_mission=org_mission,
                primary_objective=primary_objective
            )
            title = f"Constitution for {org_name}"
            
        elif document_type == 'minutes':
            org_name = request.form.get('org_name') or (organization.name if organization else "")
            meeting_date = request.form.get('meeting_date', datetime.now().strftime("%Y-%m-%d"))
            meeting_type = request.form.get('meeting_type', "Board Meeting")
            attendees = request.form.get('attendees', "").split(',') if request.form.get('attendees') else None
            
            content = doc_agent.generate_minutes(
                org_name=org_name,
                meeting_date=meeting_date,
                meeting_type=meeting_type,
                attendees=attendees
            )
            title = f"{meeting_type} Minutes - {meeting_date}"
            
        elif document_type == 'letter':
            org_name = request.form.get('org_name') or (organization.name if organization else "")
            letter_subject = request.form.get('letter_subject', "")
            letter_purpose = request.form.get('letter_purpose', "")
            recipient = request.form.get('recipient', "")
            
            content = doc_agent.generate_request_letter(
                org_name=org_name,
                letter_subject=letter_subject,
                letter_purpose=letter_purpose,
                recipient=recipient
            )
            title = f"Letter: {letter_subject}"
        
        else:
            flash('Invalid document type', 'danger')
            return redirect(url_for('registration.ai_document_generation'))
        
        # Save the generated document
        ai_document = AIGeneratedDocument(
            title=title,
            content=content,
            document_type=document_type,
            organization_id=organization_id if organization_id else None,
            user_id=current_user.id
        )
        db.session.add(ai_document)
        db.session.commit()
        
        return redirect(url_for('ai.view_document', doc_id=ai_document.id))
        
    except Exception as e:
        current_app.logger.error(f"Error generating document: {str(e)}")
        flash(f"Error generating document: {str(e)}", 'danger')
        return redirect(url_for('registration.ai_document_generation'))

@ai_bp.route('/generate_audit_methodology', methods=['POST'])
@login_required
def generate_audit_methodology():
    """Generate an audit methodology using AI"""
    try:
        org_type = request.form.get('org_type')
        ngo_type = request.form.get('ngo_type')
        focus_areas = request.form.getlist('focus_areas')
        
        # Validate inputs
        if not org_type:
            flash('Organization type is required', 'danger')
            return redirect(url_for('compliance.audit_support'))
        
        # Initialize AI agent
        audit_agent = AuditMethodologyAgent()
        
        # Generate audit methodology
        content = audit_agent.generate_audit_methodology(
            org_type=org_type,
            ngo_type=ngo_type if org_type == 'NGO' else None,
            focus_areas=focus_areas if focus_areas else None
        )
        
        title = f"Compliance Audit Methodology for {ngo_type + ' ' if ngo_type else ''}{org_type}"
        
        # Save the generated methodology
        ai_document = AIGeneratedDocument(
            title=title,
            content=content,
            document_type='Audit Methodology',
            user_id=current_user.id
        )
        db.session.add(ai_document)
        db.session.commit()
        
        return redirect(url_for('ai.view_methodology', methodology_id=ai_document.id))
        
    except Exception as e:
        current_app.logger.error(f"Error generating audit methodology: {str(e)}")
        flash(f"Error generating audit methodology: {str(e)}", 'danger')
        return redirect(url_for('compliance.audit_support'))

@ai_bp.route('/document/<int:doc_id>')
@login_required
def view_document(doc_id):
    """View an AI generated document"""
    document = AIGeneratedDocument.query.get_or_404(doc_id)
    
    # Check if user has permission to view this document
    if document.user_id != current_user.id and not current_user.role == 'admin':
        if document.organization_id is None or document.organization_id != current_user.organization_id:
            abort(403)
    
    return render_template('ai/view_document.html', document=document)

@ai_bp.route('/methodology/<int:methodology_id>')
@login_required
def view_methodology(methodology_id):
    """View an AI generated audit methodology"""
    methodology = AIGeneratedDocument.query.get_or_404(methodology_id)
    
    # Check if user has permission to view this methodology
    if methodology.user_id != current_user.id and not current_user.role == 'admin':
        if methodology.organization_id is None or methodology.organization_id != current_user.organization_id:
            abort(403)
    
    return render_template('ai/view_methodology.html', methodology=methodology)

@ai_bp.route('/download_document/<int:doc_id>')
@login_required
def download_document(doc_id):
    """Download an AI generated document as PDF"""
    document = AIGeneratedDocument.query.get_or_404(doc_id)
    
    # Check if user has permission to download this document
    if document.user_id != current_user.id and not current_user.role == 'admin':
        if document.organization_id is None or document.organization_id != current_user.organization_id:
            abort(403)
    
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{document.title}</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif;
                    font-size: 12pt;
                    line-height: 1.5;
                    margin: 2cm;
                }}
                h1 {{ font-size: 18pt; text-align: center; margin-bottom: 2cm; }}
                .footer {{ position: fixed; bottom: 0; width: 100%; text-align: center; font-size: 9pt; }}
            </style>
        </head>
        <body>
            <h1>{document.title}</h1>
            <div>{document.content}</div>
            <div class="footer">Generated by NGOmply on {document.created_at.strftime('%Y-%m-%d')}</div>
        </body>
        </html>
        """
        
        # Generate PDF
        font_config = FontConfiguration()
        html = HTML(string=html_content)
        pdf_file = html.write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 2cm }')])
        
        # Create response
        from flask import send_file
        return send_file(
            io.BytesIO(pdf_file),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{document.title.replace(' ', '_')}.pdf"
        )
        
    except Exception as e:
        current_app.logger.error(f"Error generating PDF: {str(e)}")
        flash(f"Error generating PDF: {str(e)}", 'danger')
        return redirect(url_for('ai.view_document', doc_id=doc_id))

@ai_bp.route('/download_methodology/<int:methodology_id>')
@login_required
def download_methodology(methodology_id):
    """Download an AI generated audit methodology as PDF"""
    methodology = AIGeneratedDocument.query.get_or_404(methodology_id)
    
    # Check if user has permission to download this methodology
    if methodology.user_id != current_user.id and not current_user.role == 'admin':
        if methodology.organization_id is None or methodology.organization_id != current_user.organization_id:
            abort(403)
    
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{methodology.title}</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif;
                    font-size: 12pt;
                    line-height: 1.5;
                    margin: 2cm;
                }}
                h1 {{ font-size: 18pt; text-align: center; margin-bottom: 2cm; }}
                .footer {{ position: fixed; bottom: 0; width: 100%; text-align: center; font-size: 9pt; }}
            </style>
        </head>
        <body>
            <h1>{methodology.title}</h1>
            <div>{methodology.content}</div>
            <div class="footer">Generated by NGOmply on {methodology.created_at.strftime('%Y-%m-%d')}</div>
        </body>
        </html>
        """
        
        # Generate PDF
        font_config = FontConfiguration()
        html = HTML(string=html_content)
        pdf_file = html.write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 2cm }')])
        
        # Create response
        from flask import send_file
        return send_file(
            io.BytesIO(pdf_file),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{methodology.title.replace(' ', '_')}.pdf"
        )
        
    except Exception as e:
        current_app.logger.error(f"Error generating PDF: {str(e)}")
        flash(f"Error generating PDF: {str(e)}", 'danger')
        return redirect(url_for('ai.view_methodology', methodology_id=methodology_id))
