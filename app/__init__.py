from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
import os
import logging
from logging.handlers import RotatingFileHandler

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Set up login view
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Import and register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.registration import registration_bp
    from app.routes.compliance import compliance_bp
    from app.routes.permit_renewal import permit_renewal_bp
    from app.routes.knowledge_base import knowledge_base_bp
    from app.routes.ai import ai_bp
    
    # Import and register new module blueprints
    from app.routes.subscription import subscription_bp
    from app.routes.data_protection import data_protection_bp
    from app.routes.financial import financial_bp
    from app.routes.governance import governance_bp
    from app.routes.program_compliance import program_compliance_bp
    from app.routes.analytics import analytics_bp
    from app.routes.ai_assistant import ai_assistant_bp
    from app.routes.value_added import value_added_bp
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(registration_bp, url_prefix='/registration')
    app.register_blueprint(compliance_bp, url_prefix='/compliance')
    app.register_blueprint(permit_renewal_bp, url_prefix='/permit-renewal')
    app.register_blueprint(knowledge_base_bp, url_prefix='/knowledge-base')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    
    # Register new module blueprints
    app.register_blueprint(subscription_bp, url_prefix='/subscription')
    app.register_blueprint(data_protection_bp, url_prefix='/data-protection')
    app.register_blueprint(financial_bp, url_prefix='/financial')
    app.register_blueprint(governance_bp, url_prefix='/governance')
    app.register_blueprint(program_compliance_bp, url_prefix='/program-compliance')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(ai_assistant_bp, url_prefix='/ai-assistant')
    app.register_blueprint(value_added_bp, url_prefix='/value-added')
    
    # Register error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Set up logging
    if not app.debug and not app.testing:
        # Ensure log directory exists
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Set up file handler
        file_handler = RotatingFileHandler('logs/ngomply.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        
        # Set up app logger
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('NGOmply startup')
    
    # Import models to ensure they're registered with SQLAlchemy
    from app.models import models
    from app.models import subscription_models
    from app.models import data_protection_models
    from app.models import financial_models
    from app.models import governance_models
    from app.models import program_compliance_models
    from app.models import analytics_models
    from app.models import ai_assistant_models
    from app.models import value_added_models
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
        
        # Initialize database with required data
        from app.utils.db_init import initialize_database
        initialize_database()
    
    return app

# Import user loader
from app.models.models import User

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
