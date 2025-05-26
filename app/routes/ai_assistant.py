from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app.models.ai_assistant_models import AIQuery, AIResponse, AIDocument, AIMethodology
from app.models.models import Organization, User, Document
from app.models.subscription_models import Subscription, Feature, UsageRecord, TierFeature
from app import db
from datetime import datetime, timedelta
import os
import json
import requests
from werkzeug.utils import secure_filename
from app.utils.file_handlers import allowed_file, save_file
from app.ai_agents.agents import generate_document, generate_methodology

ai_assistant_bp = Blueprint('ai_assistant', __name__)

@ai_assistant_bp.route('/')
@login_required
def index():
    """AI Compliance Assistant home page"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'ai_assistant'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Get recent queries
    recent_queries = AIQuery.query.filter_by(
        organization_id=organization.id
    ).order_by(AIQuery.created_at.desc()).limit(5).all()
    
    # Get generated documents
    documents = AIDocument.query.filter_by(
        organization_id=organization.id
    ).order_by(AIDocument.created_at.desc()).limit(5).all()
    
    # Get methodologies
    methodologies = AIMethodology.query.filter_by(
        organization_id=organization.id
    ).order_by(AIMethodology.created_at.desc()).limit(5).all()
    
    # Record feature usage
    record_feature_usage(organization.id, 'ai_assistant')
    
    return render_template('ai_assistant/index.html',
                          organization=organization,
                          recent_queries=recent_queries,
                          documents=documents,
                          methodologies=methodologies)

@ai_assistant_bp.route('/query', methods=['GET', 'POST'])
@login_required
def query():
    """Submit a compliance query to the AI assistant"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'ai_assistant_query'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        query_text = request.form.get('query_text')
        category = request.form.get('category', 'general')
        
        if not query_text:
            flash('Query text is required.', 'danger')
            return redirect(url_for('ai_assistant.query'))
        
        # Create query record
        ai_query = AIQuery(
            organization_id=organization.id,
            user_id=current_user.id,
            query_text=query_text,
            category=category,
            status='processing'
        )
        
        db.session.add(ai_query)
        db.session.commit()
        
        try:
            # Call Anthropic Claude API for response
            # In a real implementation, this would use the actual API
            # For demo purposes, generate a realistic response
            
            # Simulate API call delay
            import time
            time.sleep(1)
            
            # Generate response based on query category
            if category == 'registration':
                response_text = generate_registration_response(query_text)
            elif category == 'financial':
                response_text = generate_financial_response(query_text)
            elif category == 'governance':
                response_text = generate_governance_response(query_text)
            elif category == 'program':
                response_text = generate_program_response(query_text)
            else:
                response_text = generate_general_response(query_text)
            
            # Create response record
            ai_response = AIResponse(
                query_id=ai_query.id,
                response_text=response_text,
                model_used='claude-3-opus',
                tokens_used=calculate_tokens(query_text, response_text),
                status='completed'
            )
            
            # Update query status
            ai_query.status = 'completed'
            
            db.session.add(ai_response)
            db.session.add(ai_query)
            
            # Record feature usage
            record_feature_usage(organization.id, 'ai_assistant_query')
            
            db.session.commit()
            
            return redirect(url_for('ai_assistant.view_response', query_id=ai_query.id))
            
        except Exception as e:
            # Handle error
            ai_query.status = 'failed'
            ai_query.error_message = str(e)
            
            db.session.add(ai_query)
            db.session.commit()
            
            flash(f'Error processing query: {str(e)}', 'danger')
            return redirect(url_for('ai_assistant.query'))
    
    # Get recent queries for reference
    recent_queries = AIQuery.query.filter_by(
        organization_id=organization.id,
        status='completed'
    ).order_by(AIQuery.created_at.desc()).limit(10).all()
    
    return render_template('ai_assistant/query.html',
                          organization=organization,
                          recent_queries=recent_queries)

@ai_assistant_bp.route('/response/<int:query_id>')
@login_required
def view_response(query_id):
    """View AI assistant response"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get query
    query = AIQuery.query.get_or_404(query_id)
    
    # Check if query belongs to user's organization
    if query.organization_id != organization.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('ai_assistant.index'))
    
    # Get response
    response = AIResponse.query.filter_by(query_id=query.id).first()
    
    if not response and query.status == 'processing':
        flash('Your query is still being processed. Please check back later.', 'info')
        return redirect(url_for('ai_assistant.index'))
    
    if not response:
        flash('No response found for this query.', 'warning')
        return redirect(url_for('ai_assistant.index'))
    
    return render_template('ai_assistant/view_response.html',
                          organization=organization,
                          query=query,
                          response=response)

@ai_assistant_bp.route('/history')
@login_required
def query_history():
    """View AI query history"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all queries
    queries = AIQuery.query.filter_by(
        organization_id=organization.id
    ).order_by(AIQuery.created_at.desc()).all()
    
    return render_template('ai_assistant/query_history.html',
                          organization=organization,
                          queries=queries)

@ai_assistant_bp.route('/document/generate', methods=['GET', 'POST'])
@login_required
def generate_ai_document():
    """Generate document using AI"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'ai_document_generation'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        document_type = request.form.get('document_type')
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not document_type or not title:
            flash('Document type and title are required.', 'danger')
            return redirect(url_for('ai_assistant.generate_ai_document'))
        
        # Create document record
        ai_document = AIDocument(
            organization_id=organization.id,
            user_id=current_user.id,
            document_type=document_type,
            title=title,
            description=description,
            status='processing'
        )
        
        db.session.add(ai_document)
        db.session.commit()
        
        try:
            # Call document generation function
            document_content = generate_document(
                document_type=document_type,
                organization_name=organization.name,
                title=title,
                description=description
            )
            
            # Save document content to file
            filename = f"{document_type}_{secure_filename(title)}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.md"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ai_documents', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(document_content)
            
            # Update document record
            ai_document.file_path = file_path
            ai_document.status = 'completed'
            
            db.session.add(ai_document)
            
            # Record feature usage
            record_feature_usage(organization.id, 'ai_document_generation')
            
            db.session.commit()
            
            flash('Document generated successfully.', 'success')
            return redirect(url_for('ai_assistant.view_document', document_id=ai_document.id))
            
        except Exception as e:
            # Handle error
            ai_document.status = 'failed'
            ai_document.error_message = str(e)
            
            db.session.add(ai_document)
            db.session.commit()
            
            flash(f'Error generating document: {str(e)}', 'danger')
            return redirect(url_for('ai_assistant.generate_ai_document'))
    
    return render_template('ai_assistant/generate_document.html',
                          organization=organization)

@ai_assistant_bp.route('/document/<int:document_id>')
@login_required
def view_document(document_id):
    """View AI generated document"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get document
    document = AIDocument.query.get_or_404(document_id)
    
    # Check if document belongs to user's organization
    if document.organization_id != organization.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('ai_assistant.index'))
    
    # Read document content
    document_content = ""
    if document.file_path and os.path.exists(document.file_path):
        with open(document.file_path, 'r') as f:
            document_content = f.read()
    
    return render_template('ai_assistant/view_document.html',
                          organization=organization,
                          document=document,
                          document_content=document_content)

@ai_assistant_bp.route('/documents')
@login_required
def documents():
    """View AI generated documents"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all documents
    documents = AIDocument.query.filter_by(
        organization_id=organization.id
    ).order_by(AIDocument.created_at.desc()).all()
    
    return render_template('ai_assistant/documents.html',
                          organization=organization,
                          documents=documents)

@ai_assistant_bp.route('/methodology/generate', methods=['GET', 'POST'])
@login_required
def generate_ai_methodology():
    """Generate compliance methodology using AI"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'ai_methodology_generation'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    if request.method == 'POST':
        methodology_type = request.form.get('methodology_type')
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not methodology_type or not title:
            flash('Methodology type and title are required.', 'danger')
            return redirect(url_for('ai_assistant.generate_ai_methodology'))
        
        # Create methodology record
        ai_methodology = AIMethodology(
            organization_id=organization.id,
            user_id=current_user.id,
            methodology_type=methodology_type,
            title=title,
            description=description,
            status='processing'
        )
        
        db.session.add(ai_methodology)
        db.session.commit()
        
        try:
            # Call methodology generation function
            methodology_content = generate_methodology(
                methodology_type=methodology_type,
                organization_name=organization.name,
                title=title,
                description=description
            )
            
            # Save methodology content to file
            filename = f"{methodology_type}_{secure_filename(title)}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.md"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ai_methodologies', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(methodology_content)
            
            # Update methodology record
            ai_methodology.file_path = file_path
            ai_methodology.status = 'completed'
            
            db.session.add(ai_methodology)
            
            # Record feature usage
            record_feature_usage(organization.id, 'ai_methodology_generation')
            
            db.session.commit()
            
            flash('Methodology generated successfully.', 'success')
            return redirect(url_for('ai_assistant.view_methodology', methodology_id=ai_methodology.id))
            
        except Exception as e:
            # Handle error
            ai_methodology.status = 'failed'
            ai_methodology.error_message = str(e)
            
            db.session.add(ai_methodology)
            db.session.commit()
            
            flash(f'Error generating methodology: {str(e)}', 'danger')
            return redirect(url_for('ai_assistant.generate_ai_methodology'))
    
    return render_template('ai_assistant/generate_methodology.html',
                          organization=organization)

@ai_assistant_bp.route('/methodology/<int:methodology_id>')
@login_required
def view_methodology(methodology_id):
    """View AI generated methodology"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get methodology
    methodology = AIMethodology.query.get_or_404(methodology_id)
    
    # Check if methodology belongs to user's organization
    if methodology.organization_id != organization.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('ai_assistant.index'))
    
    # Read methodology content
    methodology_content = ""
    if methodology.file_path and os.path.exists(methodology.file_path):
        with open(methodology.file_path, 'r') as f:
            methodology_content = f.read()
    
    return render_template('ai_assistant/view_methodology.html',
                          organization=organization,
                          methodology=methodology,
                          methodology_content=methodology_content)

@ai_assistant_bp.route('/methodologies')
@login_required
def methodologies():
    """View AI generated methodologies"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get all methodologies
    methodologies = AIMethodology.query.filter_by(
        organization_id=organization.id
    ).order_by(AIMethodology.created_at.desc()).all()
    
    return render_template('ai_assistant/methodologies.html',
                          organization=organization,
                          methodologies=methodologies)

# Helper functions
def generate_registration_response(query_text):
    """Generate response for registration-related queries"""
    # In a real implementation, this would call the Anthropic Claude API
    # For demo purposes, generate a realistic response
    
    if 'requirements' in query_text.lower():
        return """
        # NGO Registration Requirements in Uganda
        
        To register an NGO in Uganda, you need to fulfill the following requirements:
        
        ## Documentation Requirements
        1. **Application Form** - Completed NGO registration form from the NGO Bureau
        2. **Constitution** - Organization's constitution in English
        3. **Workplan and Budget** - Detailed 1-3 year workplan and budget
        4. **Recommendation Letters** - From Local Council and District NGO Monitoring Committee
        5. **Proof of Payment** - Registration fee receipt (currently UGX 100,000)
        
        ## Organizational Requirements
        1. **Board of Directors** - At least 5 members with diverse backgrounds
        2. **Physical Address** - Verifiable physical address in Uganda
        3. **Bank Account** - Organizational bank account with a recognized financial institution
        
        ## Process Timeline
        The registration process typically takes 45-60 days if all documentation is in order.
        
        ## Common Challenges
        - Incomplete documentation is the most common reason for delays
        - Inconsistencies between constitution and workplan
        - Inadequate financial controls in the constitution
        
        Would you like me to provide more specific information about any of these requirements?
        """
    
    elif 'renewal' in query_text.lower():
        return """
        # NGO Permit Renewal Process in Uganda
        
        NGO permits in Uganda must be renewed every 5 years. Here's the process:
        
        ## Required Documents
        1. **Renewal Application Form** - Available from the NGO Bureau
        2. **Annual Returns** - Proof of submission for all operational years
        3. **Audit Reports** - Financial audit reports for the permit period
        4. **Activity Reports** - Summary of activities conducted during the permit period
        5. **Tax Clearance** - From Uganda Revenue Authority
        6. **Renewal Fee Receipt** - Currently UGX 80,000
        
        ## Timeline
        - Submit renewal application at least 3 months before expiry
        - Processing typically takes 30-45 days
        
        ## Important Notes
        - Operating with an expired permit is illegal and can result in deregistration
        - Ensure all annual returns are up to date before applying for renewal
        - Address any compliance issues raised in previous monitoring visits
        
        ## Recent Changes
        As of 2024, the NGO Bureau has introduced an online renewal system that streamlines the process. You can access it at https://ngobureau.go.ug/
        
        Would you like specific guidance on preparing any of these documents?
        """
    
    else:
        return """
        # NGO Registration in Uganda
        
        NGO registration in Uganda is governed by the Non-Governmental Organizations Act, 2016 and is managed by the NGO Bureau under the Ministry of Internal Affairs.
        
        ## Registration Process Overview
        1. **Reserve Name** - First check name availability and reserve your organization name
        2. **Prepare Documentation** - Develop constitution, workplan, and budget
        3. **Local Approvals** - Obtain recommendation letters from local authorities
        4. **Submit Application** - File complete application with the NGO Bureau
        5. **Verification** - NGO Bureau conducts verification of information
        6. **Approval** - Board reviews and approves application
        7. **Certificate Issuance** - Receive registration certificate and permit
        
        ## Types of Registration
        - **National NGO** - Operating in more than one district
        - **Community Based Organization (CBO)** - Operating in one district
        - **International NGO** - Foreign-based organization
        
        ## Compliance Requirements
        After registration, NGOs must:
        - Submit annual returns
        - Maintain proper financial records
        - Comply with the NGO Act and Regulations
        - Renew permits every 5 years
        
        For specific questions about your registration needs, please provide more details about your organization type and operational scope.
        """

def generate_financial_response(query_text):
    """Generate response for financial compliance queries"""
    # In a real implementation, this would call the Anthropic Claude API
    # For demo purposes, generate a realistic response
    
    if 'audit' in query_text.lower():
        return """
        # NGO Financial Audit Requirements in Uganda
        
        ## Audit Requirements
        1. **Annual Audits** - All registered NGOs must conduct annual financial audits
        2. **Qualified Auditors** - Must use auditors certified by the Institute of Certified Public Accountants of Uganda (ICPAU)
        3. **Audit Scope** - Must cover all financial activities, internal controls, and compliance with applicable laws
        
        ## Audit Report Components
        1. **Financial Statements** - Including balance sheet, income statement, cash flow statement
        2. **Auditor's Opinion** - Independent assessment of financial statements
        3. **Management Letter** - Highlighting internal control weaknesses and recommendations
        4. **Compliance Statement** - Confirming adherence to relevant laws and regulations
        
        ## Submission Requirements
        1. **NGO Bureau** - Submit within 6 months after the end of the financial year
        2. **Uganda Revenue Authority** - If the NGO has tax exemption status
        3. **Donors** - As per specific donor requirements
        
        ## Common Audit Findings
        1. Inadequate financial policies and procedures
        2. Poor documentation of expenses
        3. Weak internal controls
        4. Improper asset management
        5. Non-compliance with donor restrictions
        
        ## Best Practices
        1. Maintain detailed financial records throughout the year
        2. Implement strong internal control systems
        3. Conduct regular internal audits
        4. Address previous audit findings promptly
        5. Ensure board oversight of financial management
        
        Would you like specific guidance on preparing for an audit or addressing common findings?
        """
    
    elif 'tax' in query_text.lower():
        return """
        # NGO Tax Compliance in Uganda
        
        ## Tax Exemption Status
        NGOs in Uganda can apply for tax exemption status, but this is not automatic upon registration.
        
        ## Application Process for Tax Exemption
        1. **Submit Application** to Uganda Revenue Authority (URA)
        2. **Required Documents**:
           - NGO registration certificate
           - Constitution showing charitable objectives
           - Financial statements
           - Activity reports demonstrating public benefit
        3. **Review Process** - URA reviews application and may conduct site visits
        4. **Certificate Issuance** - If approved, tax exemption certificate is issued
        
        ## Taxes Applicable to NGOs
        Even with exemption status, NGOs must comply with:
        
        1. **PAYE (Pay As You Earn)** - For all employees
        2. **Withholding Tax** - On payments to contractors and service providers
        3. **Local Service Tax** - For employees based on salary scale
        
        ## Filing Requirements
        1. **Monthly Returns** - PAYE and withholding tax by 15th of following month
        2. **Annual Returns** - By June 30th each year
        3. **Tax Clearance Certificate** - Required annually for permit renewal
        
        ## Common Compliance Issues
        1. Failure to withhold taxes on payments to suppliers
        2. Late filing of returns
        3. Incorrect classification of exempt vs. non-exempt activities
        4. Poor documentation of tax-exempt expenditures
        
        ## Recent Changes
        As of 2024, URA has implemented the Electronic Fiscal Receipting and Invoicing Solution (EFRIS) which NGOs must use for all financial transactions.
        
        Would you like specific guidance on any of these tax compliance areas?
        """
    
    else:
        return """
        # NGO Financial Compliance in Uganda
        
        Financial compliance for NGOs in Uganda involves several key areas:
        
        ## Regulatory Framework
        1. **NGO Act 2016** - Requires proper financial management and annual audits
        2. **Anti-Money Laundering Act** - Requires due diligence in financial transactions
        3. **Financial Intelligence Authority (FIA) Guidelines** - For preventing terrorism financing
        
        ## Key Compliance Requirements
        1. **Financial Management System** - Proper accounting system with adequate controls
        2. **Annual Budgeting** - Board-approved annual budget aligned with workplan
        3. **Financial Reporting** - Regular internal reports and annual external reporting
        4. **Annual Audits** - Conducted by ICPAU-certified auditors
        5. **Tax Compliance** - PAYE, withholding tax, and other applicable taxes
        6. **Annual Returns** - Financial statements submitted to NGO Bureau
        
        ## Best Practices
        1. **Financial Policies** - Comprehensive policies covering procurement, travel, etc.
        2. **Segregation of Duties** - Different individuals responsible for different financial functions
        3. **Documentation** - Proper documentation for all financial transactions
        4. **Bank Reconciliation** - Regular reconciliation of bank statements
        5. **Asset Management** - Proper recording and management of assets
        6. **Budget Monitoring** - Regular comparison of actual vs. budgeted expenses
        
        ## Common Compliance Gaps
        1. Inadequate financial policies
        2. Poor record keeping
        3. Lack of board oversight on finances
        4. Commingling of donor funds
        5. Inadequate supporting documentation
        
        For specific guidance on your organization's financial compliance needs, please provide more details about your operations and current financial management practices.
        """

def generate_governance_response(query_text):
    """Generate response for governance-related queries"""
    # In a real implementation, this would call the Anthropic Claude API
    # For demo purposes, generate a realistic response
    
    if 'board' in query_text.lower():
        return """
        # NGO Board Governance Requirements in Uganda
        
        ## Board Composition Requirements
        1. **Minimum Size** - At least 5 board members for registered NGOs
        2. **Diversity** - Gender and professional diversity recommended
        3. **Independence** - Majority should be independent (non-staff)
        4. **Ugandan Representation** - For international NGOs, at least 1/3 should be Ugandan nationals
        
        ## Board Responsibilities
        1. **Strategic Direction** - Setting organizational vision and strategy
        2. **Financial Oversight** - Approving budgets and ensuring financial accountability
        3. **Policy Approval** - Developing and approving key organizational policies
        4. **Executive Oversight** - Hiring and evaluating the Executive Director
        5. **Compliance Monitoring** - Ensuring adherence to laws and regulations
        6. **Risk Management** - Identifying and mitigating organizational risks
        
        ## Meeting Requirements
        1. **Frequency** - Minimum quarterly meetings (recommended)
        2. **Documentation** - Proper minutes recording decisions and actions
        3. **Quorum** - As defined in the organization's constitution (typically >50%)
        
        ## Best Practices
        1. **Term Limits** - Typically 2-3 years, renewable once or twice
        2. **Committees** - Finance, Programs, and Governance committees
        3. **Conflict of Interest Policy** - Written policy with annual declarations
        4. **Board Evaluation** - Annual self-assessment of board performance
        5. **Succession Planning** - For board leadership positions
        
        ## Common Governance Gaps
        1. Inactive or rubber-stamp boards
        2. Lack of clear separation between board and management
        3. Inadequate financial oversight
        4. Poor documentation of board decisions
        5. Conflicts of interest not properly managed
        
        Would you like specific guidance on improving your board governance practices?
        """
    
    elif 'conflict of interest' in query_text.lower():
        return """
        # Managing Conflicts of Interest in Ugandan NGOs
        
        ## Regulatory Requirements
        The NGO Act 2016 and Regulations require NGOs to have mechanisms for managing conflicts of interest among board members and staff.
        
        ## Key Elements of a Conflict of Interest Policy
        1. **Definition** - Clear definition of what constitutes a conflict of interest
        2. **Disclosure Mechanism** - Process for declaring potential conflicts
        3. **Documentation** - Recording of disclosures and actions taken
        4. **Recusal Procedure** - Process for removing conflicted individuals from decision-making
        5. **Consequences** - Clear consequences for undisclosed conflicts
        
        ## Implementation Steps
        1. **Develop Policy** - Create a comprehensive conflict of interest policy
        2. **Annual Declarations** - Require annual written declarations from board and senior staff
        3. **Meeting Procedures** - Include conflict disclosure as a standing agenda item
        4. **Register** - Maintain a register of declared interests
        5. **Training** - Educate board and staff on identifying and managing conflicts
        
        ## Common Conflict Situations in NGOs
        1. Board member providing paid services to the organization
        2. Hiring relatives of board or senior staff
        3. Procurement from businesses connected to board/staff
        4. Board members serving on boards of similar organizations
        5. Receiving personal benefits from organizational partnerships
        
        ## Sample Disclosure Form Sections
        1. Business relationships with the organization
        2. Family relationships with staff or other board members
        3. Volunteer or paid roles with similar organizations
        4. Significant financial interests in entities dealing with the NGO
        5. Gifts or favors received from individuals seeking benefits from the NGO
        
        Would you like a template conflict of interest policy or disclosure form tailored to Ugandan NGO requirements?
        """
    
    else:
        return """
        # NGO Governance Compliance in Uganda
        
        Good governance is essential for NGO compliance in Uganda and is scrutinized by the NGO Bureau during registration, monitoring visits, and permit renewals.
        
        ## Key Governance Requirements
        1. **Governing Documents** - Clear constitution with governance provisions
        2. **Board Structure** - Properly constituted board with defined roles
        3. **Decision-Making** - Transparent and documented decision processes
        4. **Policies** - Core governance policies in place and implemented
        5. **Accountability** - Mechanisms for accountability to stakeholders
        
        ## Essential Governance Policies
        1. **Financial Management Policy** - Controls, approvals, reporting
        2. **Human Resource Policy** - Recruitment, compensation, conduct
        3. **Conflict of Interest Policy** - Disclosure and management procedures
        4. **Procurement Policy** - Fair and transparent procurement processes
        5. **Whistleblower Policy** - Protection for those reporting misconduct
        
        ## Governance Best Practices
        1. **Regular Board Meetings** - With proper documentation
        2. **Board-Management Separation** - Clear distinction of roles
        3. **Stakeholder Engagement** - Including beneficiary feedback mechanisms
        4. **Succession Planning** - For board and senior management
        5. **Transparency** - In operations and decision-making
        6. **Regular Policy Review** - Updating policies to reflect current needs
        
        ## Common Governance Findings in NGO Bureau Inspections
        1. Inactive boards with no meeting minutes
        2. Founder syndrome (excessive control by founders)
        3. Lack of key governance policies
        4. Poor documentation of board decisions
        5. Inadequate financial oversight by the board
        
        For specific guidance on improving your organization's governance, please provide more details about your current structure and practices.
        """

def generate_program_response(query_text):
    """Generate response for program compliance queries"""
    # In a real implementation, this would call the Anthropic Claude API
    # For demo purposes, generate a realistic response
    
    if 'local government' in query_text.lower():
        return """
        # NGO Compliance with Local Government Requirements in Uganda
        
        ## Local Government Engagement Requirements
        1. **Memorandum of Understanding (MOU)** - Required with district local governments where you operate
        2. **Work Plan Sharing** - Annual work plans must be shared with District NGO Monitoring Committees
        3. **Activity Reporting** - Quarterly activity reports to be submitted to district authorities
        4. **Coordination Meetings** - Participation in district coordination meetings
        5. **Local Taxes and Fees** - Compliance with any applicable local government fees
        
        ## MOU Process
        1. **Initial Engagement** - Meet with Chief Administrative Officer (CAO)
        2. **Documentation** - Submit organization profile, registration, work plan
        3. **Draft Review** - Local government reviews and may suggest changes
        4. **Signing** - Formal signing ceremony with district leadership
        5. **Renewal** - Typically every 3-5 years or with new strategic plans
        
        ## District NGO Monitoring Committee
        This committee oversees NGO activities and includes:
        - Chief Administrative Officer (Chair)
        - District Community Development Officer
        - District Internal Security Officer
        - Representatives from local NGOs
        
        ## Common Compliance Issues
        1. Operating without formal MOUs
        2. Failure to attend coordination meetings
        3. Inconsistent reporting to local authorities
        4. Not aligning activities with district development plans
        5. Bypassing local structures in program implementation
        
        ## Best Practices
        1. Engage early with local authorities when entering a new district
        2. Maintain regular communication beyond formal requirements
        3. Align programs with district development priorities
        4. Document all interactions with local government officials
        5. Participate actively in district-level NGO forums
        
        Would you like specific guidance on developing an MOU or improving local government relations?
        """
    
    elif 'permit' in query_text.lower():
        return """
        # Sector-Specific Permits for NGOs in Uganda
        
        Beyond the NGO Bureau registration, organizations working in specific sectors require additional permits and approvals:
        
        ## Health Sector
        1. **Ministry of Health Approval** - Required for all health-related interventions
        2. **District Health Officer Clearance** - For local health activities
        3. **Medical Council Registration** - For operating health facilities
        4. **National Drug Authority Permits** - For medication distribution
        
        ## Education Sector
        1. **Ministry of Education Approval** - For educational programs
        2. **District Education Officer Clearance** - For school-based activities
        3. **National Curriculum Development Centre** - For curriculum materials
        
        ## Environment Sector
        1. **NEMA Approval** - For environmental interventions
        2. **Environmental Impact Assessment** - For projects affecting natural resources
        3. **Forestry Department Clearance** - For forestry-related activities
        
        ## Child-Focused Programs
        1. **Ministry of Gender, Labour and Social Development** - Approval for child-focused programs
        2. **Probation and Social Welfare Office** - Local-level approval
        3. **Special Clearance** - For child protection and residential care
        
        ## Application Process General Steps
        1. **Initial Consultation** - Meet with relevant ministry/department
        2. **Documentation Submission** - Including NGO registration, program details
        3. **Site Visits** - Officials may inspect proposed activity locations
        4. **Technical Review** - By subject matter experts in the ministry
        5. **Approval Issuance** - Formal permit or letter of no objection
        
        ## Compliance Maintenance
        1. **Regular Reporting** - Typically quarterly to relevant ministries
        2. **Permit Renewal** - Usually annually or biannually
        3. **Compliance Visits** - Expect monitoring visits from authorities
        
        Would you like specific information about permits for a particular sector?
        """
    
    else:
        return """
        # Program Compliance for NGOs in Uganda
        
        Program compliance involves ensuring your NGO's activities adhere to both general NGO regulations and sector-specific requirements.
        
        ## General Program Compliance Requirements
        1. **Alignment with Registration** - Programs must align with registered objectives
        2. **Geographic Restrictions** - Operations limited to approved districts
        3. **Work Plan Approval** - Annual work plans should be approved by the board
        4. **Activity Reporting** - Regular reporting to NGO Bureau and local governments
        5. **Beneficiary Protection** - Safeguarding policies for vulnerable beneficiaries
        
        ## Sector-Specific Compliance
        Different sectors have additional requirements:
        - **Health** - Ministry of Health approvals and standards
        - **Education** - Ministry of Education guidelines and approvals
        - **Child Protection** - Special permits and safeguarding requirements
        - **Environment** - NEMA approvals and environmental impact assessments
        - **Agriculture** - Ministry of Agriculture standards and approvals
        
        ## Local Government Compliance
        1. **Memorandum of Understanding** - Required with district governments
        2. **Coordination** - Participation in district coordination mechanisms
        3. **Alignment** - Programs should align with district development plans
        
        ## Donor Compliance
        While not regulatory, donor requirements often include:
        1. **Specific Reporting** - According to donor templates and schedules
        2. **Procurement Standards** - Often stricter than local requirements
        3. **M&E Systems** - Robust monitoring and evaluation
        4. **Visibility Guidelines** - For acknowledging donor support
        
        ## Common Program Compliance Issues
        1. Mission drift (activities outside registered objectives)
        2. Operating in districts not covered by permit
        3. Lack of proper sector-specific permits
        4. Inadequate beneficiary protection measures
        5. Poor coordination with government programs
        
        For specific guidance on your program compliance needs, please provide details about your program areas and operational locations.
        """

def generate_general_response(query_text):
    """Generate response for general compliance queries"""
    # In a real implementation, this would call the Anthropic Claude API
    # For demo purposes, generate a realistic response
    
    if 'data protection' in query_text.lower():
        return """
        # Data Protection Compliance for NGOs in Uganda
        
        ## Regulatory Framework
        The Data Protection and Privacy Act 2019 governs how organizations collect, process, and store personal data in Uganda.
        
        ## Key Compliance Requirements
        1. **Registration** - Data collectors/processors must register with the Personal Data Protection Office
        2. **Consent** - Must obtain clear consent before collecting personal data
        3. **Purpose Limitation** - Collect data only for specified, explicit purposes
        4. **Data Minimization** - Collect only what's necessary for your purpose
        5. **Accuracy** - Ensure data is accurate and up-to-date
        6. **Storage Limitation** - Keep data only as long as necessary
        7. **Security** - Implement appropriate security measures
        8. **Data Subject Rights** - Honor rights to access, correct, and delete data
        
        ## NGO-Specific Considerations
        1. **Beneficiary Data** - Special care for vulnerable populations
        2. **Health Data** - Additional protections for health information
        3. **Children's Data** - Parental consent requirements
        4. **Donor Data** - Proper handling of donor information
        5. **Cross-border Transfers** - Rules for sharing data with international partners
        
        ## Implementation Steps
        1. **Data Audit** - Inventory what personal data you collect and process
        2. **Privacy Policy** - Develop and publish your privacy policy
        3. **Consent Mechanisms** - Implement proper consent collection
        4. **Security Measures** - Encrypt sensitive data, limit access
        5. **Staff Training** - Train staff on data protection principles
        6. **Breach Response Plan** - Procedure for handling data breaches
        
        ## Registration Process
        1. Complete the PDPO registration form (available at https://www.nita.go.ug/)
        2. Pay registration fee (currently UGX 100,000)
        3. Submit data protection impact assessment for high-risk processing
        4. Receive registration certificate (valid for 1 year)
        
        Would you like specific guidance on any aspect of data protection compliance?
        """
    
    elif 'annual returns' in query_text.lower():
        return """
        # NGO Annual Returns Requirements in Uganda
        
        ## Filing Requirements
        All registered NGOs must submit annual returns to the NGO Bureau within 6 months after the end of each financial year.
        
        ## Required Documents
        1. **Form F** - The official annual return form
        2. **Annual Report** - Narrative report of activities
        3. **Financial Statements** - Audited by ICPAU-certified auditor
        4. **Tax Clearance** - From Uganda Revenue Authority
        5. **Updated Board Information** - If changes occurred
        6. **Updated Staff List** - With positions and nationalities
        7. **Asset Inventory** - List of organizational assets
        
        ## Submission Process
        1. **Compile Documents** - Gather all required documents
        2. **Board Approval** - Get board approval for annual report and financial statements
        3. **Complete Form F** - Available from NGO Bureau website
        4. **Submit Package** - To NGO Bureau offices or online portal
        5. **Receipt** - Obtain acknowledgment of submission
        
        ## Common Compliance Issues
        1. Late submission (after 6-month deadline)
        2. Incomplete documentation
        3. Financial statements not audited by certified auditor
        4. Inconsistencies between narrative and financial reports
        5. Missing tax clearance certificate
        
        ## Consequences of Non-Compliance
        1. **Warning** - Initial notice of non-compliance
        2. **Fines** - Monetary penalties for continued non-compliance
        3. **Permit Issues** - Problems during permit renewal
        4. **Deregistration** - For persistent non-compliance
        
        ## Best Practices
        1. Start preparation 3 months before deadline
        2. Maintain good records throughout the year
        3. Schedule audit well in advance
        4. Review previous submission feedback
        5. Keep copies of all submitted documents
        
        Would you like a checklist for preparing your annual returns or guidance on addressing specific compliance issues?
        """
    
    else:
        return """
        # NGO Compliance Overview in Uganda
        
        NGO compliance in Uganda involves adhering to multiple regulatory frameworks:
        
        ## Key Regulatory Bodies
        1. **NGO Bureau** - Primary regulator for NGO registration and operations
        2. **Financial Intelligence Authority** - Monitors financial transactions
        3. **Uganda Revenue Authority** - Tax compliance
        4. **National Social Security Fund** - Employee benefits compliance
        5. **Relevant Line Ministries** - Sector-specific compliance
        
        ## Core Compliance Areas
        1. **Registration Compliance**
           - Valid NGO permit
           - Operating within registered objectives
           - Geographic restrictions
           
        2. **Financial Compliance**
           - Proper financial management systems
           - Annual audits
           - Tax compliance (PAYE, withholding tax)
           - Anti-money laundering measures
           
        3. **Governance Compliance**
           - Functioning board structure
           - Regular board meetings
           - Clear policies and procedures
           - Conflict of interest management
           
        4. **Program Compliance**
           - Alignment with registered objectives
           - Sector-specific permits and standards
           - Local government coordination
           - Beneficiary protection
           
        5. **Reporting Compliance**
           - Annual returns to NGO Bureau
           - Tax returns to URA
           - Reports to local governments
           - Donor reporting
        
        ## Recent Regulatory Changes
        1. **Online Registration System** - NGO Bureau has digitized registration
        2. **Risk-Based Monitoring** - Increased focus on high-risk organizations
        3. **Financial Intelligence Requirements** - Enhanced due diligence
        4. **Data Protection** - New requirements under Data Protection Act
        
        ## Compliance Calendar
        - **Quarterly** - Local government reports
        - **Monthly** - PAYE and withholding tax returns
        - **Annually** - NGO Bureau returns, audit, tax clearance
        - **Every 5 Years** - NGO permit renewal
        
        For specific guidance on your compliance needs, please provide more details about your organization type, activities, and specific compliance concerns.
        """

def calculate_tokens(query_text, response_text):
    """Calculate approximate token usage"""
    # In a real implementation, this would use the actual token count from the API
    # For demo purposes, use a simple approximation
    
    # Rough approximation: 1 token ≈ 4 characters
    query_tokens = len(query_text) // 4
    response_tokens = len(response_text) // 4
    
    return query_tokens + response_tokens

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
