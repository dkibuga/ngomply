from app import db
from datetime import datetime

class SubscriptionTier(db.Model):
    """Model for subscription tiers with feature limits"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)  # e.g., Free, Basic, Premium, Enterprise
    description = db.Column(db.Text)
    price_monthly = db.Column(db.Float)
    price_yearly = db.Column(db.Float)
    max_users = db.Column(db.Integer)
    max_documents = db.Column(db.Integer)
    max_storage_mb = db.Column(db.Integer)
    max_ai_generations = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='tier', lazy='dynamic')
    features = db.relationship('TierFeature', backref='tier', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SubscriptionTier {self.name}>'

class Feature(db.Model):
    """Model for system features that can be enabled/disabled per tier"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    module = db.Column(db.String(50))  # e.g., compliance, data_protection, financial, etc.
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tier_features = db.relationship('TierFeature', backref='feature', lazy='dynamic')
    
    def __repr__(self):
        return f'<Feature {self.name}>'

class TierFeature(db.Model):
    """Association model between tiers and features"""
    id = db.Column(db.Integer, primary_key=True)
    tier_id = db.Column(db.Integer, db.ForeignKey('subscription_tier.id'))
    feature_id = db.Column(db.Integer, db.ForeignKey('feature.id'))
    is_enabled = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<TierFeature {self.tier_id}:{self.feature_id}>'

class Subscription(db.Model):
    """Model for organization subscriptions"""
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    tier_id = db.Column(db.Integer, db.ForeignKey('subscription_tier.id'))
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed, cancelled
    payment_method = db.Column(db.String(50), nullable=True)
    auto_renew = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='subscription')
    usage_records = db.relationship('UsageRecord', backref='subscription', lazy='dynamic')
    
    def __repr__(self):
        return f'<Subscription {self.organization_id}:{self.tier_id}>'

class UsageRecord(db.Model):
    """Model for tracking feature usage"""
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'))
    feature_id = db.Column(db.Integer, db.ForeignKey('feature.id'))
    count = db.Column(db.Integer, default=1)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    
    # Relationship
    feature = db.relationship('Feature')
    
    def __repr__(self):
        return f'<UsageRecord {self.subscription_id}:{self.feature_id}>'

class Voucher(db.Model):
    """Model for subscription vouchers/grants"""
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True)
    tier_id = db.Column(db.Integer, db.ForeignKey('subscription_tier.id'))
    discount_percent = db.Column(db.Integer, default=100)  # 100% = fully subsidized
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    max_uses = db.Column(db.Integer, default=1)
    current_uses = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    sponsor_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tier = db.relationship('SubscriptionTier')
    creator = db.relationship('User')
    redemptions = db.relationship('VoucherRedemption', backref='voucher', lazy='dynamic')
    
    def __repr__(self):
        return f'<Voucher {self.code}>'

class VoucherRedemption(db.Model):
    """Model for tracking voucher usage"""
    id = db.Column(db.Integer, primary_key=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('voucher.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'))
    redeemed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization')
    subscription = db.relationship('Subscription')
    
    def __repr__(self):
        return f'<VoucherRedemption {self.voucher_id}:{self.organization_id}>'

class SessionTracker(db.Model):
    """Model for tracking concurrent user sessions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    session_id = db.Column(db.String(100), unique=True)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    user = db.relationship('User', backref='sessions')
    
    def __repr__(self):
        return f'<SessionTracker {self.user_id}:{self.session_id}>'
