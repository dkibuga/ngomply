from app.utils.db_init import initialize_database
from app.models.subscription_models import Tier, Feature, TierFeature
from app.models.value_added_models import ConsultingService, TrainingService
from app import db
from datetime import datetime, timedelta

def initialize_database():
    """Initialize database with required data for new modules"""
    # Check if initialization is needed
    if Tier.query.first() is not None:
        # Already initialized
        return
    
    # Create subscription tiers
    freemium = Tier(
        name='Freemium',
        description='Basic access to essential resources',
        price=0,
        max_users=2,
        max_documents=10,
        max_concurrent_sessions=1,
        is_active=True
    )
    
    basic = Tier(
        name='Basic',
        description='Standard access for small NGOs',
        price=50000,  # UGX
        max_users=5,
        max_documents=50,
        max_concurrent_sessions=2,
        is_active=True
    )
    
    professional = Tier(
        name='Professional',
        description='Enhanced access for medium-sized NGOs',
        price=150000,  # UGX
        max_users=15,
        max_documents=200,
        max_concurrent_sessions=5,
        is_active=True
    )
    
    enterprise = Tier(
        name='Enterprise',
        description='Comprehensive access for large NGOs',
        price=300000,  # UGX
        max_users=50,
        max_documents=1000,
        max_concurrent_sessions=10,
        is_active=True
    )
    
    db.session.add_all([freemium, basic, professional, enterprise])
    db.session.commit()
    
    # Create features
    features = [
        # Core features
        Feature(name='knowledge_base_access', display_name='Knowledge Base Access', description='Access to compliance knowledge base'),
        Feature(name='document_templates', display_name='Document Templates', description='Access to standard document templates'),
        Feature(name='compliance_reminders', display_name='Compliance Reminders', description='Automated compliance reminders'),
        
        # Data Protection features
        Feature(name='data_protection_assessment', display_name='Data Protection Assessment', description='Data protection impact assessment tools'),
        Feature(name='consent_management', display_name='Consent Management', description='Tools for managing consent collection and tracking'),
        Feature(name='data_breach_notification', display_name='Data Breach Notification', description='Templates and procedures for data breach notification'),
        Feature(name='pdpo_registration', display_name='PDPO Registration', description='Personal Data Protection Office registration workflow'),
        
        # Financial Compliance features
        Feature(name='financial_reporting', display_name='Financial Reporting', description='Financial reporting templates and tools'),
        Feature(name='audit_preparation', display_name='Audit Preparation', description='Tools for preparing for financial audits'),
        Feature(name='budget_tracking', display_name='Budget Tracking', description='Budget vs. actual tracking with compliance flags'),
        Feature(name='tax_exemption', display_name='Tax Exemption', description='Tax exemption documentation management'),
        
        # Governance features
        Feature(name='board_management', display_name='Board Management', description='Tools for managing board documentation and meetings'),
        Feature(name='policy_templates', display_name='Policy Templates', description='Templates for organizational policies'),
        Feature(name='conflict_of_interest', display_name='Conflict of Interest', description='Conflict of interest management tools'),
        Feature(name='governance_assessment', display_name='Governance Assessment', description='Governance assessment tools'),
        
        # Program Compliance features
        Feature(name='sector_compliance', display_name='Sector Compliance', description='Sector-specific compliance requirements database'),
        Feature(name='program_checklists', display_name='Program Checklists', description='Program-level compliance checklists'),
        Feature(name='ministry_reporting', display_name='Ministry Reporting', description='Ministry-specific reporting templates'),
        Feature(name='local_permits', display_name='Local Permits', description='Local government permit management'),
        
        # Analytics features
        Feature(name='compliance_dashboard', display_name='Compliance Dashboard', description='Compliance analytics dashboard'),
        Feature(name='deadline_tracking', display_name='Deadline Tracking', description='Deadline tracking with predictive alerts'),
        Feature(name='compliance_trends', display_name='Compliance Trends', description='Compliance trend analysis'),
        Feature(name='risk_prediction', display_name='Risk Prediction', description='Risk prediction algorithms'),
        
        # AI Assistant features
        Feature(name='ai_assistant', display_name='AI Assistant', description='AI-powered compliance assistant'),
        Feature(name='ai_document_generation', display_name='AI Document Generation', description='AI-powered document generation'),
        Feature(name='ai_methodology_generation', display_name='AI Methodology Generation', description='AI-powered compliance methodology generation'),
        
        # Value-Added Services features
        Feature(name='consulting_services', display_name='Consulting Services', description='Access to consulting services'),
        Feature(name='training_services', display_name='Training Services', description='Access to training services'),
        Feature(name='audit_support', display_name='Audit Support', description='Support during audits'),
        Feature(name='financial_review', display_name='Financial Review', description='Financial review services')
    ]
    
    db.session.add_all(features)
    db.session.commit()
    
    # Assign features to tiers
    # Freemium tier features
    freemium_features = [
        ('knowledge_base_access', None),  # Unlimited
        ('document_templates', 5),        # 5 templates per month
        ('compliance_reminders', 3)       # 3 reminders per month
    ]
    
    # Basic tier features
    basic_features = [
        ('knowledge_base_access', None),  # Unlimited
        ('document_templates', 20),       # 20 templates per month
        ('compliance_reminders', 10),     # 10 reminders per month
        ('data_protection_assessment', 1), # 1 assessment per month
        ('consent_management', 5),        # 5 consent forms per month
        ('financial_reporting', 2),       # 2 reports per month
        ('policy_templates', 5),          # 5 templates per month
        ('program_checklists', 3),        # 3 checklists per month
        ('compliance_dashboard', None),   # Unlimited
        ('ai_assistant', 10)              # 10 queries per month
    ]
    
    # Professional tier features
    professional_features = [
        ('knowledge_base_access', None),  # Unlimited
        ('document_templates', 50),       # 50 templates per month
        ('compliance_reminders', 30),     # 30 reminders per month
        ('data_protection_assessment', 3), # 3 assessments per month
        ('consent_management', 20),       # 20 consent forms per month
        ('data_breach_notification', 2),  # 2 notifications per month
        ('pdpo_registration', 1),         # 1 registration per month
        ('financial_reporting', 5),       # 5 reports per month
        ('audit_preparation', 1),         # 1 preparation per month
        ('budget_tracking', None),        # Unlimited
        ('tax_exemption', 2),             # 2 documents per month
        ('board_management', None),       # Unlimited
        ('policy_templates', 15),         # 15 templates per month
        ('conflict_of_interest', 5),      # 5 forms per month
        ('governance_assessment', 1),     # 1 assessment per month
        ('sector_compliance', 3),         # 3 sectors per month
        ('program_checklists', 10),       # 10 checklists per month
        ('ministry_reporting', 3),        # 3 reports per month
        ('local_permits', 2),             # 2 permits per month
        ('compliance_dashboard', None),   # Unlimited
        ('deadline_tracking', None),      # Unlimited
        ('compliance_trends', None),      # Unlimited
        ('ai_assistant', 30),             # 30 queries per month
        ('ai_document_generation', 5),    # 5 documents per month
        ('consulting_services', 1),       # 1 consultation per month
        ('training_services', 1)          # 1 training per month
    ]
    
    # Enterprise tier features
    enterprise_features = [
        ('knowledge_base_access', None),  # Unlimited
        ('document_templates', None),     # Unlimited
        ('compliance_reminders', None),   # Unlimited
        ('data_protection_assessment', None), # Unlimited
        ('consent_management', None),     # Unlimited
        ('data_breach_notification', 5),  # 5 notifications per month
        ('pdpo_registration', 3),         # 3 registrations per month
        ('financial_reporting', None),    # Unlimited
        ('audit_preparation', 3),         # 3 preparations per month
        ('budget_tracking', None),        # Unlimited
        ('tax_exemption', 5),             # 5 documents per month
        ('board_management', None),       # Unlimited
        ('policy_templates', None),       # Unlimited
        ('conflict_of_interest', None),   # Unlimited
        ('governance_assessment', 3),     # 3 assessments per month
        ('sector_compliance', None),      # Unlimited
        ('program_checklists', None),     # Unlimited
        ('ministry_reporting', None),     # Unlimited
        ('local_permits', 5),             # 5 permits per month
        ('compliance_dashboard', None),   # Unlimited
        ('deadline_tracking', None),      # Unlimited
        ('compliance_trends', None),      # Unlimited
        ('risk_prediction', None),        # Unlimited
        ('ai_assistant', None),           # Unlimited
        ('ai_document_generation', 20),   # 20 documents per month
        ('ai_methodology_generation', 5), # 5 methodologies per month
        ('consulting_services', 3),       # 3 consultations per month
        ('training_services', 3),         # 3 trainings per month
        ('audit_support', 1),             # 1 support per month
        ('financial_review', 1)           # 1 review per month
    ]
    
    # Add features to tiers
    for feature_name, limit in freemium_features:
        feature = Feature.query.filter_by(name=feature_name).first()
        tier_feature = TierFeature(
            tier_id=freemium.id,
            feature_id=feature.id,
            is_enabled=True,
            usage_limit=limit
        )
        db.session.add(tier_feature)
    
    for feature_name, limit in basic_features:
        feature = Feature.query.filter_by(name=feature_name).first()
        tier_feature = TierFeature(
            tier_id=basic.id,
            feature_id=feature.id,
            is_enabled=True,
            usage_limit=limit
        )
        db.session.add(tier_feature)
    
    for feature_name, limit in professional_features:
        feature = Feature.query.filter_by(name=feature_name).first()
        tier_feature = TierFeature(
            tier_id=professional.id,
            feature_id=feature.id,
            is_enabled=True,
            usage_limit=limit
        )
        db.session.add(tier_feature)
    
    for feature_name, limit in enterprise_features:
        feature = Feature.query.filter_by(name=feature_name).first()
        tier_feature = TierFeature(
            tier_id=enterprise.id,
            feature_id=feature.id,
            is_enabled=True,
            usage_limit=limit
        )
        db.session.add(tier_feature)
    
    # Create consulting services
    consulting_services = [
        ConsultingService(
            name='NGO Registration Consulting',
            description='Expert guidance through the NGO registration process',
            price=200000,  # UGX
            duration=14,   # days
            is_active=True
        ),
        ConsultingService(
            name='Compliance Audit Preparation',
            description='Preparation for compliance audits by regulatory authorities',
            price=350000,  # UGX
            duration=21,   # days
            is_active=True
        ),
        ConsultingService(
            name='Financial Systems Review',
            description='Review and recommendations for financial management systems',
            price=400000,  # UGX
            duration=30,   # days
            is_active=True
        ),
        ConsultingService(
            name='Governance Structure Assessment',
            description='Assessment and recommendations for governance structures',
            price=300000,  # UGX
            duration=21,   # days
            is_active=True
        ),
        ConsultingService(
            name='Data Protection Compliance',
            description='Guidance on compliance with data protection regulations',
            price=250000,  # UGX
            duration=14,   # days
            is_active=True
        )
    ]
    
    db.session.add_all(consulting_services)
    
    # Create training services
    training_services = [
        TrainingService(
            name='NGO Compliance Fundamentals',
            description='Fundamentals of NGO compliance in Uganda',
            price=150000,  # UGX
            duration=1,    # days
            max_participants=20,
            is_active=True
        ),
        TrainingService(
            name='Financial Management for NGOs',
            description='Financial management best practices for NGOs',
            price=200000,  # UGX
            duration=2,    # days
            max_participants=15,
            is_active=True
        ),
        TrainingService(
            name='Board Governance Workshop',
            description='Effective governance for NGO boards',
            price=180000,  # UGX
            duration=1,    # days
            max_participants=15,
            is_active=True
        ),
        TrainingService(
            name='Data Protection for NGOs',
            description='Implementing data protection in NGO operations',
            price=150000,  # UGX
            duration=1,    # days
            max_participants=20,
            is_active=True
        ),
        TrainingService(
            name='Donor Compliance Requirements',
            description='Understanding and meeting donor compliance requirements',
            price=250000,  # UGX
            duration=2,    # days
            max_participants=15,
            is_active=True
        )
    ]
    
    db.session.add_all(training_services)
    db.session.commit()
