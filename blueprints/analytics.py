from flask import Blueprint, render_template, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Species, SpeciesSighting, Achievement, UserProgress, User
from sqlalchemy import func, desc, case
from datetime import datetime, timedelta
from app import db

analytics = Blueprint('analytics', __name__)

@analytics.route('/analytics/dashboard')
@login_required
def dashboard():
    if current_user.role != 'teacher':
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('main.dashboard'))
    return render_template('analytics/dashboard.html')

@analytics.route('/api/analytics/species-status')
@login_required
def species_status_data():
    try:
        # Aggregate species by conservation status
        species_counts = db.session.query(
            Species.conservation_status,
            func.count(Species.id).label('count')
        ).filter(Species.conservation_status.isnot(None))\
         .group_by(Species.conservation_status).all()

        result = {
            'labels': [status[0] or 'Unknown' for status in species_counts],
            'data': [status[1] for status in species_counts]
        }

        return jsonify(result)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)})

@analytics.route('/api/analytics/sightings-trend')
@login_required
def sightings_trend_data():
    try:
        # Get sightings for the last 6 months with status
        six_months_ago = datetime.utcnow() - timedelta(days=180)

        monthly_sightings = db.session.query(
            func.date_trunc('month', SpeciesSighting.sighting_date).label('month'),
            SpeciesSighting.status,
            func.count(SpeciesSighting.id).label('count')
        ).filter(
            SpeciesSighting.sighting_date >= six_months_ago
        ).group_by('month', SpeciesSighting.status)\
         .order_by('month').all()

        # Process data for stacked chart
        months = sorted(set(m[0] for m in monthly_sightings))

        result = {
            'labels': [m.strftime('%B %Y') for m in months],
            'datasets': [
                {
                    'label': 'Verified',
                    'data': [next((s[2] for s in monthly_sightings 
                                if s[0] == m and s[1] == 'verified'), 0)
                            for m in months]
                },
                {
                    'label': 'Pending',
                    'data': [next((s[2] for s in monthly_sightings 
                                if s[0] == m and s[1] == 'pending'), 0)
                            for m in months]
                },
                {
                    'label': 'Rejected',
                    'data': [next((s[2] for s in monthly_sightings 
                                if s[0] == m and s[1] == 'rejected'), 0)
                            for m in months]
                }
            ]
        }

        return jsonify(result)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)})

@analytics.route('/api/analytics/achievement-distribution')
@login_required
def achievement_distribution():
    try:
        # Get achievement distribution by category with student counts
        achievement_data = db.session.query(
            Achievement.category,
            func.count(Achievement.id).label('total'),
            func.count(func.distinct(Achievement.user_id)).label('students')
        ).filter(Achievement.category.isnot(None))\
         .group_by(Achievement.category)\
         .order_by(desc('total')).all()

        result = {
            'labels': [ach[0] or 'Uncategorized' for ach in achievement_data],
            'datasets': [
                {
                    'label': 'Total Achievements',
                    'data': [ach[1] for ach in achievement_data]
                },
                {
                    'label': 'Students Achieved',
                    'data': [ach[2] for ach in achievement_data]
                }
            ]
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'labels': [],
            'datasets': []
        })

@analytics.route('/api/analytics/student-progress')
@login_required
def student_progress_analytics():
    try:
        # Get overall progress statistics for students
        progress_stats = db.session.query(
            User.username,
            func.count(UserProgress.id).label('total_items'),
            func.sum(
                case([(UserProgress.completed, 1)], else_=0)
            ).label('completed_items')
        ).join(UserProgress)\
         .filter(User.role == 'student')\
         .group_by(User.username)\
         .order_by(desc('completed_items')).all()

        result = {
            'labels': [stat[0] for stat in progress_stats],
            'datasets': [
                {
                    'label': 'Completed Items',
                    'data': [stat[2] or 0 for stat in progress_stats]
                },
                {
                    'label': 'Total Items',
                    'data': [stat[1] for stat in progress_stats]
                }
            ]
        }

        return jsonify(result)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)})