from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from models import Species, PopulationRecord, HabitatData, MigrationPattern
from app import db, app

advanced_analytics = Blueprint('advanced_analytics', __name__)

@advanced_analytics.route('/analytics/population-trends')
@login_required
def population_trends():
    """View population trends for species over time"""
    if current_user.role != 'teacher':
        return render_template('errors/403.html'), 403
    return render_template('analytics/population_trends.html')

@advanced_analytics.route('/api/analytics/population-data')
@login_required
def population_data():
    try:
        # Get population data for each species over time
        six_months_ago = datetime.utcnow() - timedelta(days=180)

        # First get all species with population records
        species_with_records = db.session.query(Species.id, Species.name)\
            .join(PopulationRecord)\
            .group_by(Species.id, Species.name)\
            .having(func.count(PopulationRecord.id) > 0)\
            .all()

        if not species_with_records:
            app.logger.warning("No species found with population records")
            return jsonify({
                'labels': [],
                'datasets': [],
                'message': 'No population data available'
            })

        # Get all unique dates for records in the last 6 months
        dates = db.session.query(
            func.date_trunc('day', PopulationRecord.record_date).label('date')
        ).filter(
            PopulationRecord.record_date >= six_months_ago
        ).group_by('date').order_by('date').all()

        date_strings = [d.date.strftime('%Y-%m-%d') for d in dates]

        # Prepare datasets for each species
        datasets = []
        colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']

        for idx, (species_id, species_name) in enumerate(species_with_records):
            # Get population records for this species
            records = db.session.query(
                func.date_trunc('day', PopulationRecord.record_date).label('date'),
                func.avg(PopulationRecord.population_count).label('count')
            ).filter(
                PopulationRecord.species_id == species_id,
                PopulationRecord.record_date >= six_months_ago
            ).group_by('date').order_by('date').all()

            # Create a dict for easy lookup
            record_dict = {r.date.strftime('%Y-%m-%d'): round(r.count) for r in records}

            # Create dataset with null for missing dates
            dataset = {
                'label': species_name,
                'data': [record_dict.get(date, None) for date in date_strings],
                'borderColor': colors[idx % len(colors)],
                'backgroundColor': colors[idx % len(colors)],
                'fill': False,
                'tension': 0.4
            }
            datasets.append(dataset)

        app.logger.info(f"Successfully retrieved population data for {len(datasets)} species")
        return jsonify({
            'labels': date_strings,
            'datasets': datasets
        })

    except Exception as e:
        app.logger.error(f"Error in population_data: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Failed to retrieve population data',
            'details': str(e)
        })

@advanced_analytics.route('/analytics/habitat-analysis')
@login_required
def habitat_analysis():
    """View habitat analysis data"""
    if current_user.role != 'teacher':
        return render_template('errors/403.html'), 403
    return render_template('analytics/habitat_analysis.html')

@advanced_analytics.route('/api/analytics/habitat-data')
@login_required
def habitat_data():
    try:
        # Get habitat quality scores by type
        habitat_scores = db.session.query(
            HabitatData.habitat_type,
            func.avg(HabitatData.quality_score).label('avg_score'),
            func.count(HabitatData.id).label('count')
        ).group_by(HabitatData.habitat_type).all()

        if not habitat_scores:
            return jsonify({
                'labels': [],
                'datasets': [],
                'message': 'No habitat data available'
            })

        return jsonify({
            'labels': [h.habitat_type for h in habitat_scores],
            'datasets': [{
                'label': 'Average Habitat Quality',
                'data': [float(h.avg_score) for h in habitat_scores],
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1
            }]
        })
    except Exception as e:
        app.logger.error(f"Error in habitat_data: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Failed to retrieve habitat data',
            'details': str(e)
        })

@advanced_analytics.route('/api/analytics/migration-data')
@login_required
def migration_data():
    try:
        # Get migration patterns by species
        migration_data = db.session.query(
            Species.name,
            MigrationPattern.pattern_type,
            MigrationPattern.start_location,
            MigrationPattern.end_location,
            MigrationPattern.distance
        ).join(MigrationPattern)\
         .order_by(Species.name).all()

        if not migration_data:
            return jsonify({
                'species': [],
                'patterns': [],
                'distances': [],
                'message': 'No migration data available'
            })

        result = {
            'species': [item.name for item in migration_data],
            'patterns': [item.pattern_type for item in migration_data],
            'distances': [float(item.distance) if item.distance else 0 for item in migration_data]
        }

        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error in migration_data: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Failed to retrieve migration data',
            'details': str(e)
        })