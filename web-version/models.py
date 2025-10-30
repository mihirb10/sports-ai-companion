from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint, Text
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    display_name = db.Column(db.String, nullable=True)
    custom_avatar_path = db.Column(db.String, nullable=True)
    fantasy_scoring_system = db.Column(db.String, nullable=True)
    fantasy_roster = db.Column(Text, nullable=True)
    espn_league_id = db.Column(db.String, nullable=True)
    espn_s2 = db.Column(db.String, nullable=True)
    espn_swid = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade='all, delete-orphan')

class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    history = db.Column(Text, nullable=False, default='[]')
    fantasy_context = db.Column(Text, nullable=False, default='{"my_team": [], "interested_players": [], "trade_history": []}')
    recent_analysis_context = db.Column(Text, nullable=False, default='{}')
    last_injury_check = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class Prediction(db.Model):
    __tablename__ = 'predictions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    prediction_text = db.Column(Text, nullable=False)
    outcome = db.Column(db.String, nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.now)
    settled_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref='predictions')

class ErrorLog(db.Model):
    __tablename__ = 'error_logs'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    error_type = db.Column(db.String, nullable=False, index=True)  # 'frontend' or 'backend'
    message = db.Column(Text, nullable=False)
    stack_trace = db.Column(Text, nullable=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    url = db.Column(db.String, nullable=True)
    user_agent = db.Column(db.String, nullable=True)
    severity = db.Column(db.String, nullable=True, default='error')  # 'error', 'warning', 'critical'
    context = db.Column(Text, nullable=True)  # JSON string for additional context
    resolved = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='error_logs')
