import os
import json
from datetime import datetime
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret")

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {"check_same_thread": False}
}

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Add custom Jinja2 filters
@app.template_filter('from_json')
def from_json_filter(value):
    try:
        return json.loads(value) if value else {}
    except:
        return {}

@app.template_filter('timeago')
def timeago_filter(value):
    """Format a date time to a human readable time ago string"""
    if not value:
        return ''

    now = datetime.utcnow()
    diff = now - value

    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"
    if diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    if diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    if diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    return "just now"

# Register blueprints
from blueprints.auth import auth
from blueprints.main import main
from blueprints.species import species
from blueprints.education import education
from blueprints.programs import programs
from blueprints.games import games
from blueprints.sightings import sightings
from blueprints.library import library
from blueprints.progress import progress
from blueprints.messaging import messaging
from blueprints.profile import profile
from blueprints.analytics import analytics
from blueprints.school import school
from blueprints.forum import forum
from blueprints.advanced_analytics import advanced_analytics
from blueprints.gamification import gamification

# Register all blueprints
blueprints = [
    auth, main, species, education, programs, games,
    sightings, library, progress, messaging, profile,
    analytics, school, forum, advanced_analytics, gamification
]

for blueprint in blueprints:
    app.register_blueprint(blueprint)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f'Page not found: {error}')
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'Server Error: {error}')
    return render_template('errors/500.html'), 500

# Initialize database and data
with app.app_context():
    try:
        # Import models after app creation to avoid circular imports
        import models  # noqa: F401
        db.create_all()
        app.logger.info('Database tables created successfully')

        # Initialize default data
        from scripts.init_data import init_data
        init_data()
        app.logger.info('Default data initialized successfully')
    except Exception as e:
        app.logger.error(f'Error during startup: {e}')