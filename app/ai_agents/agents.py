import os
import anthropic
from flask import current_app
from datetime import datetime

class AIAgent:
    """Base class for AI agents using Anthropic Claude"""
    
    def __init__(self):
        """Initialize the AI agent with Anthropic Claude client"""
        api_key = current_app.config.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        self.client = anthropic.Anthropic(api_key=api_key)
        
    def _generate_response(self, prompt, max_tokens=2000, model="claude-3-opus-20240229"):
        """
        Generate a response from Claude
        
        Args:
            prompt (str): The prompt to send to Claude
            max_tokens (int, optional): Maximum tokens in response. Defaults to 2000.
            model (str, optional): Claude model to use. Defaults to "claude-3-opus-20240229".
            
        Returns:
            str: The generated response
        """
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            current_app.logger.error(f"Error generating AI response: {str(e)}")
            return f"Error generating content: {str(e)}"

class DocumentGenerationAgent(AIAgent):
    """AI agent for document generation"""
    
    def generate_constitution(self, org_name, org_vision, org_mission, primary_objective):
        """
        Generate an organization constitution
        
        Args:
            org_name (str): Organization name
            org_vision (str): Organization vision
            org_mission (str): Organization mission
            primary_objective (str): Primary objective
            
        Returns:
            str: Generated constitution
        """
        prompt = f"""
        Generate a comprehensive constitution for an NGO/CBO in Uganda with the following details:
        
        Organization Name: {org_name}
        Vision: {org_vision}
        Mission: {org_mission}
        Primary Objective: {primary_objective}
        
        The constitution should include:
        1. Name, Vision, Mission, and Objectives
        2. Membership criteria and procedures
        3. Governance structure (Board/Executive Committee)
        4. Meetings and procedures
        5. Financial management
        6. Amendment procedures
        7. Dissolution procedures
        
        Format the constitution professionally with proper numbering and sections.
        """
        
        return self._generate_response(prompt, max_tokens=4000)
    
    def generate_minutes(self, org_name, meeting_date, meeting_type, attendees=None):
        """
        Generate meeting minutes
        
        Args:
            org_name (str): Organization name
            meeting_date (str): Meeting date
            meeting_type (str): Type of meeting
            attendees (list, optional): List of attendees. Defaults to None.
            
        Returns:
            str: Generated minutes
        """
        attendees_str = ", ".join(attendees) if attendees else "Board members and key staff"
        
        prompt = f"""
        Generate professional meeting minutes for the following meeting:
        
        Organization: {org_name}
        Date: {meeting_date}
        Meeting Type: {meeting_type}
        Attendees: {attendees_str}
        
        Include the following sections:
        1. Call to order
        2. Approval of previous minutes
        3. Reports (financial, program updates)
        4. Old business
        5. New business
        6. Announcements
        7. Adjournment
        
        Make the content realistic and professional, with appropriate details for an NGO/CBO in Uganda.
        """
        
        return self._generate_response(prompt, max_tokens=3000)
    
    def generate_request_letter(self, org_name, letter_subject, letter_purpose, recipient=None):
        """
        Generate a formal request letter
        
        Args:
            org_name (str): Organization name
            letter_subject (str): Subject of the letter
            letter_purpose (str): Purpose of the request
            recipient (str, optional): Letter recipient. Defaults to None.
            
        Returns:
            str: Generated letter
        """
        recipient = recipient or "The NGO Bureau"
        current_date = datetime.now().strftime("%d %B, %Y")
        
        prompt = f"""
        Generate a formal request letter with the following details:
        
        From: {org_name}
        To: {recipient}
        Date: {current_date}
        Subject: {letter_subject}
        Purpose: {letter_purpose}
        
        Format the letter professionally with appropriate salutation, introduction, body paragraphs explaining the request, 
        conclusion, and closing. The tone should be formal and respectful, appropriate for communication with government 
        authorities in Uganda.
        """
        
        return self._generate_response(prompt, max_tokens=2000)

class AuditMethodologyAgent(AIAgent):
    """AI agent for generating compliance audit methodologies"""
    
    def generate_audit_methodology(self, org_type, ngo_type=None, focus_areas=None):
        """
        Generate a compliance audit methodology
        
        Args:
            org_type (str): Organization type (NGO or CBO)
            ngo_type (str, optional): Type of NGO. Defaults to None.
            focus_areas (list, optional): Areas to focus on. Defaults to None.
            
        Returns:
            str: Generated audit methodology
        """
        org_type_str = f"{org_type}"
        if org_type == "NGO" and ngo_type:
            org_type_str = f"{ngo_type} {org_type}"
            
        focus_areas_str = ", ".join(focus_areas) if focus_areas else "governance, financial management, program implementation, and reporting"
        
        prompt = f"""
        Generate a comprehensive compliance audit methodology for a {org_type_str} in Uganda, focusing on {focus_areas_str}.
        
        The methodology should include:
        
        1. Introduction and Purpose
           - Scope and objectives of the audit
           - Regulatory framework applicable to {org_type_str}s in Uganda
        
        2. Pre-Audit Planning
           - Document review checklist
           - Stakeholder identification
           - Risk assessment approach
        
        3. Audit Procedures
           - Governance compliance checks
           - Financial compliance verification
           - Operational compliance assessment
           - Reporting compliance evaluation
        
        4. Evidence Collection Methods
           - Document sampling methodology
           - Interview protocols
           - Observation techniques
        
        5. Compliance Scoring System
           - Rating criteria
           - Compliance thresholds
           - Non-compliance categorization
        
        6. Reporting Framework
           - Report structure
           - Finding classification
           - Recommendation formulation
        
        7. Follow-up Procedures
           - Remediation timeline
           - Verification process
        
        Make the methodology practical, detailed, and aligned with Ugandan NGO/CBO regulatory requirements.
        """
        
        return self._generate_response(prompt, max_tokens=4000)
