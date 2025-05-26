import os
import anthropic
from flask import current_app, jsonify
import logging
from datetime import datetime

class AIAgent:
    """Base class for AI agents using Anthropic Claude"""
    
    def __init__(self, api_key=None):
        """
        Initialize the AI agent
        
        Args:
            api_key (str, optional): Anthropic API key. Defaults to None (uses environment variable).
        """
        try:
            self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY') or current_app.config.get('ANTHROPIC_API_KEY')
            if not self.api_key:
                raise ValueError("Anthropic API key not found. Please set ANTHROPIC_API_KEY environment variable or provide it in the application config.")
            
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-3-opus-20240229"  # Default to most capable model
            self.logger = logging.getLogger(__name__)
            
        except Exception as e:
            self.logger.error(f"Error initializing AI agent: {str(e)}")
            raise

    def _call_api(self, prompt, max_tokens=1000, temperature=0.7):
        """
        Call the Anthropic API with error handling
        
        Args:
            prompt (str): Prompt to send to the API
            max_tokens (int, optional): Maximum tokens to generate. Defaults to 1000.
            temperature (float, optional): Temperature for generation. Defaults to 0.7.
            
        Returns:
            str: Generated text
            
        Raises:
            Exception: If API call fails
        """
        try:
            # Log API call attempt
            self.logger.info(f"Calling Anthropic API with prompt length: {len(prompt)}")
            
            # Make API call with timeout and retry logic
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract and validate response
            if not response or not hasattr(response, 'content') or not response.content:
                raise ValueError("Empty or invalid response from Anthropic API")
                
            # Get the text content from the response
            content = response.content[0].text if hasattr(response.content[0], 'text') else ""
            
            # Log successful API call
            self.logger.info(f"Anthropic API call successful, received {len(content)} characters")
            
            return content
            
        except anthropic.APIError as e:
            self.logger.error(f"Anthropic API error: {str(e)}")
            raise Exception(f"AI service error: {str(e)}")
            
        except anthropic.APITimeoutError as e:
            self.logger.error(f"Anthropic API timeout: {str(e)}")
            raise Exception("AI service timeout. Please try again later.")
            
        except anthropic.APIConnectionError as e:
            self.logger.error(f"Anthropic API connection error: {str(e)}")
            raise Exception("Unable to connect to AI service. Please check your internet connection.")
            
        except anthropic.APIStatusError as e:
            self.logger.error(f"Anthropic API status error: {str(e)}")
            raise Exception(f"AI service returned an error: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Unexpected error calling Anthropic API: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")

    def validate_response(self, response):
        """
        Validate AI response
        
        Args:
            response (str): Response to validate
            
        Returns:
            bool: True if response is valid, False otherwise
        """
        # Check if response is empty
        if not response or len(response.strip()) < 10:
            self.logger.warning("AI returned empty or very short response")
            return False
            
        # Check for error messages in response
        error_indicators = ["I'm sorry", "I apologize", "I cannot", "I'm unable to"]
        if any(indicator in response for indicator in error_indicators):
            self.logger.warning(f"AI response contains error indicators: {response[:100]}...")
            return False
            
        return True


class DocumentGenerationAgent(AIAgent):
    """AI agent for document generation"""
    
    def generate_constitution(self, org_name, org_vision="", org_mission="", primary_objective=""):
        """
        Generate an organization constitution
        
        Args:
            org_name (str): Name of the organization
            org_vision (str, optional): Vision statement. Defaults to "".
            org_mission (str, optional): Mission statement. Defaults to "".
            primary_objective (str, optional): Primary objective. Defaults to "".
            
        Returns:
            str: Generated constitution
        """
        try:
            prompt = f"""
            Generate a comprehensive constitution for a Ugandan NGO/CBO named "{org_name}".
            
            Organization details:
            - Name: {org_name}
            - Vision: {org_vision if org_vision else 'To be determined by the organization'}
            - Mission: {org_mission if org_mission else 'To be determined by the organization'}
            - Primary Objective: {primary_objective if primary_objective else 'To be determined by the organization'}
            
            The constitution should include the following sections:
            1. Name, Vision, Mission, and Objectives
            2. Legal Status and Registered Office
            3. Membership (categories, rights, obligations)
            4. Governance Structure (board, committees)
            5. Meetings (general assembly, board meetings)
            6. Financial Management
            7. Amendment Procedures
            8. Dissolution
            
            Format the constitution professionally with proper numbering and section headers.
            Ensure it complies with Ugandan NGO laws and regulations.
            """
            
            response = self._call_api(prompt, max_tokens=2000, temperature=0.2)
            
            # Validate response
            if not self.validate_response(response):
                raise Exception("Failed to generate a valid constitution. Please try again with more specific details.")
                
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating constitution: {str(e)}")
            raise Exception(f"Error generating constitution: {str(e)}")

    def generate_minutes(self, org_name, meeting_date, meeting_type="Board Meeting", attendees=None):
        """
        Generate meeting minutes
        
        Args:
            org_name (str): Name of the organization
            meeting_date (str): Date of the meeting
            meeting_type (str, optional): Type of meeting. Defaults to "Board Meeting".
            attendees (list, optional): List of attendees. Defaults to None.
            
        Returns:
            str: Generated minutes
        """
        try:
            attendees_str = ", ".join(attendees) if attendees else "Board members and key stakeholders"
            
            prompt = f"""
            Generate professional meeting minutes for a {meeting_type} of "{org_name}" held on {meeting_date}.
            
            Meeting details:
            - Organization: {org_name}
            - Date: {meeting_date}
            - Type: {meeting_type}
            - Attendees: {attendees_str}
            
            The minutes should include:
            1. Call to order
            2. Attendance
            3. Approval of previous minutes
            4. Reports (financial, program updates)
            5. Old business
            6. New business
            7. Announcements
            8. Adjournment
            
            Format the minutes professionally with proper structure and formatting.
            Include realistic but generic agenda items appropriate for an NGO/CBO in Uganda.
            """
            
            response = self._call_api(prompt, max_tokens=1500, temperature=0.3)
            
            # Validate response
            if not self.validate_response(response):
                raise Exception("Failed to generate valid meeting minutes. Please try again with more specific details.")
                
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating minutes: {str(e)}")
            raise Exception(f"Error generating minutes: {str(e)}")

    def generate_request_letter(self, org_name, letter_subject, letter_purpose, recipient):
        """
        Generate a request letter
        
        Args:
            org_name (str): Name of the organization
            letter_subject (str): Subject of the letter
            letter_purpose (str): Purpose of the letter
            recipient (str): Recipient of the letter
            
        Returns:
            str: Generated letter
        """
        try:
            prompt = f"""
            Generate a formal request letter from "{org_name}" to "{recipient}" regarding "{letter_subject}".
            
            Letter details:
            - Organization: {org_name}
            - Subject: {letter_subject}
            - Purpose: {letter_purpose}
            - Recipient: {recipient}
            
            The letter should:
            1. Follow formal business letter format
            2. Include today's date ({datetime.now().strftime('%B %d, %Y')})
            3. Have a professional and respectful tone
            4. Clearly state the purpose and request
            5. Include appropriate closing and signature block
            
            Format the letter professionally with proper structure and formatting.
            """
            
            response = self._call_api(prompt, max_tokens=1000, temperature=0.3)
            
            # Validate response
            if not self.validate_response(response):
                raise Exception("Failed to generate a valid request letter. Please try again with more specific details.")
                
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating request letter: {str(e)}")
            raise Exception(f"Error generating request letter: {str(e)}")


class AuditMethodologyAgent(AIAgent):
    """AI agent for audit methodology generation"""
    
    def generate_audit_methodology(self, org_type, ngo_type=None, focus_areas=None):
        """
        Generate an audit methodology
        
        Args:
            org_type (str): Type of organization (NGO, CBO)
            ngo_type (str, optional): Type of NGO. Defaults to None.
            focus_areas (list, optional): Focus areas of the organization. Defaults to None.
            
        Returns:
            str: Generated audit methodology
        """
        try:
            focus_areas_str = ", ".join(focus_areas) if focus_areas else "various social and development areas"
            org_type_full = f"{ngo_type} {org_type}" if ngo_type else org_type
            
            prompt = f"""
            Generate a comprehensive compliance audit methodology for a Ugandan {org_type_full} focused on {focus_areas_str}.
            
            The audit methodology should include:
            
            1. Introduction and Purpose
               - Scope and objectives of the compliance audit
               - Relevant legal framework for {org_type} in Uganda
            
            2. Pre-Audit Planning
               - Document collection requirements
               - Stakeholder identification
               - Risk assessment approach
            
            3. Compliance Areas to Audit
               - Governance and organizational structure
               - Financial management and reporting
               - Program implementation and monitoring
               - Human resources and employment practices
               - Asset management
               - Regulatory reporting requirements
            
            4. Audit Procedures
               - Document review methods
               - Interview protocols
               - Sampling methodology
               - Evidence collection and documentation
            
            5. Reporting and Follow-up
               - Audit report structure
               - Finding classification system
               - Corrective action planning
               - Follow-up procedures
            
            Format the methodology professionally with proper structure, headings, and subheadings.
            Include specific references to Ugandan NGO laws and regulations where appropriate.
            """
            
            response = self._call_api(prompt, max_tokens=2000, temperature=0.2)
            
            # Validate response
            if not self.validate_response(response):
                raise Exception("Failed to generate a valid audit methodology. Please try again with more specific details.")
                
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating audit methodology: {str(e)}")
            raise Exception(f"Error generating audit methodology: {str(e)}")
