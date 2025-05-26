# NGOmply - User Documentation

## Overview
NGOmply is a Python-based Software as a Service (SaaS) application designed to assist Non-Governmental Organizations (NGOs) and Community Based Organizations (CBOs) in Uganda with their legal and operational compliance obligations. The system provides a centralized platform to manage the entire compliance lifecycle, addressing key challenges such as navigating complex regulations and administrative burdens.

## System Architecture
NGOmply is built using the Flask framework with a modular structure:

- **Backend**: Python/Flask with SQLAlchemy ORM
- **Database**: SQLite (for prototype; can be migrated to PostgreSQL for production)
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **AI Integration**: OpenAI API for document generation and audit methodology creation

## Modules

### 1. Registration Module
Guides NGOs and CBOs through their respective initial registration processes with relevant authorities.

Features:
- Step-by-step registration guidance
- Digital forms and templates
- Document checklist generation
- AI document generation
- Statutory document storage

### 2. Operational Compliance Module
Supports NGOs and CBOs in maintaining ongoing compliance with legal and regulatory obligations.

Features:
- Obligation tracking
- Automated reminders and alerts
- Due diligence and risk management support
- Record keeping
- Tax and sectoral compliance tracking
- Compliance audit support
- AI audit methodology generation

### 3. Permit Renewal Module
Streamlines the process of renewing organization permits.

Features:
- Automated reminders for permit expiry
- Document aggregation
- Renewal checklist generation
- Fee information management
- Forms and links access
- Step-by-step guidance wizard

### 4. Knowledge Base Module
Dynamic repository of essential information on the Ugandan NGO/CBO regulatory environment.

Features:
- Centralized information repository
- Regular updates mechanism
- Search and access functionality
- Integration with AI agent

## AI Agent Integration

The system includes two AI agents:

1. **Document Generation Agent**: Assists users in drafting key documents such as constitutions, minutes, and formal request letters.

2. **Audit Methodology Agent**: Generates tailored compliance audit methodologies based on the most current legal and regulatory framework.

## Installation and Setup

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Virtual environment (recommended)

### Installation Steps

1. Clone the repository:
```
git clone https://github.com/yourusername/ngomply.git
cd ngomply
```

2. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-api-key
```

5. Initialize the database:
```
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. Run the application:
```
python run.py
```

7. Access the application at http://localhost:5000

## Usage Guide

### User Registration and Login
1. Navigate to the registration page
2. Create a new account with username, email, and password
3. Log in with your credentials

### Organization Registration
1. Navigate to the Registration Module
2. Complete the organization registration form
3. Follow the step-by-step guidance for document preparation
4. Upload required documents

### Compliance Management
1. Navigate to the Operational Compliance Module
2. Generate compliance reminders based on your organization type
3. Track and complete compliance tasks
4. Use the AI audit methodology generator for compliance audits

### Permit Renewal
1. Navigate to the Permit Renewal Module
2. Update your permit information
3. Follow the renewal wizard steps
4. Aggregate necessary documents for renewal

### Knowledge Base
1. Navigate to the Knowledge Base Module
2. Browse legal documents and forms
3. Search for specific information
4. Access guides for registration, compliance, and renewal

## Customization and Extension

### Adding New Forms
Administrators can update forms through the admin interface or by directly modifying the database.

### Updating Legal Information
The Knowledge Base can be updated with new legal documents and regulations as they become available.

### AI Integration
The AI agents can be customized by modifying the prompt templates in the `ai_agents` module.

## Troubleshooting

### Common Issues
- **Database errors**: Ensure your database is properly initialized
- **AI generation failures**: Verify your OpenAI API key is valid
- **Form submission errors**: Check for required fields and validation issues

### Support
For additional support, please contact support@ngomply.com

## Future Enhancements
- Integration with URSB online name reservation portal
- Mobile application for on-the-go compliance management
- Advanced reporting and analytics
- Multi-language support
