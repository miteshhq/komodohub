from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import (
    db, User, Achievement, AchievementLevel, 
    ConservationChallenge, UserChallenge,
    Species, SpeciesSighting
)
from datetime import datetime, timedelta
import json
from sqlalchemy import func, desc

gamification = Blueprint('gamification', __name__)

@gamification.route('/challenges')
@login_required
def challenges_dashboard():
    """Display available challenges and user progress"""
    # Get active species identification challenges
    species_challenges = SpeciesIdentificationChallenge.query\
        .filter_by(is_active=True)\
        .order_by(SpeciesIdentificationChallenge.difficulty)\
        .limit(5)\
        .all()
    
    # Get user's ongoing challenges
    user_challenges = UserChallenge.query\
        .filter_by(user_id=current_user.id, status='in_progress')\
        .all()
    
    # Get user's achievement progress
    achievements = Achievement.query\
        .join(AchievementLevel)\
        .filter(Achievement.user_id == current_user.id)\
        .all()
    
    return render_template('gamification/dashboard.html',
                         species_challenges=species_challenges,
                         user_challenges=user_challenges,
                         achievements=achievements)

@gamification.route('/species-identification')
@login_required
def species_identification():
    """Interactive species identification game"""
    # Get a random challenge the user hasn't attempted recently
    subquery = db.session.query(UserSpeciesIdentification.challenge_id)\
        .filter(UserSpeciesIdentification.user_id == current_user.id)\
        .filter(UserSpeciesIdentification.attempt_date >= datetime.utcnow() - timedelta(days=1))
    
    challenge = SpeciesIdentificationChallenge.query\
        .filter(~SpeciesIdentificationChallenge.id.in_(subquery))\
        .filter_by(is_active=True)\
        .order_by(db.func.random())\
        .first()
    
    if not challenge:
        flash('No new challenges available at the moment. Please try again later.', 'info')
        return redirect(url_for('gamification.challenges_dashboard'))
    
    return render_template('gamification/species_identification.html', challenge=challenge)

@gamification.route('/submit-identification', methods=['POST'])
@login_required
def submit_identification():
    """Handle species identification submission"""
    challenge_id = request.form.get('challenge_id')
    answer = request.form.get('answer')
    
    challenge = SpeciesIdentificationChallenge.query.get_or_404(challenge_id)
    is_correct = answer.lower() == challenge.correct_answer.lower()
    points_earned = challenge.points if is_correct else 0
    
    # Record the attempt
    attempt = UserSpeciesIdentification(
        user_id=current_user.id,
        challenge_id=challenge_id,
        is_correct=is_correct,
        points_earned=points_earned
    )
    db.session.add(attempt)
    
    # Update user points if correct
    if is_correct:
        current_user.points = (current_user.points or 0) + points_earned
        flash(f'Correct! You earned {points_earned} points!', 'success')
        num_achievements_unlocked = check_and_award_achievement(current_user.id, "species_identification", points_earned)
        if num_achievements_unlocked > 0:
            flash(f'You unlocked {num_achievements_unlocked} achievement(s)!', 'success')
    
    else:
        flash('Incorrect answer. Try another challenge!', 'warning')
    
    db.session.commit()
    return redirect(url_for('gamification.species_identification'))



@gamification.route('/conservation-challenges')
@login_required
def conservation_challenges():
    """Display available conservation challenges and user progress"""
    try:
        # Get active challenges filtered by difficulty
        beginner_challenges = ConservationChallenge.query\
            .filter_by(is_active=True, difficulty='easy')\
            .order_by(ConservationChallenge.created_at.desc())\
            .all()
        
        intermediate_challenges = ConservationChallenge.query\
            .filter_by(is_active=True, difficulty='medium')\
            .order_by(ConservationChallenge.created_at.desc())\
            .all()
        
        advanced_challenges = ConservationChallenge.query\
            .filter_by(is_active=True, difficulty='hard')\
            .order_by(ConservationChallenge.created_at.desc())\
            .all()
        
        # Get user's active challenges with error handling
        try:
            user_challenges = UserChallenge.query\
                .filter_by(user_id=current_user.id, status='in_progress')\
                .all()
        except Exception as e:
            app.logger.error(f"Error fetching user challenges: {str(e)}")
            user_challenges = []
        
        # Get user's completed challenges with error handling
        try:
            completed_challenges = UserChallenge.query\
                .filter_by(user_id=current_user.id, status='completed')\
                .order_by(UserChallenge.completed_at.desc())\
                .all()
        except Exception as e:
            app.logger.error(f"Error fetching completed challenges: {str(e)}")
            completed_challenges = []
        
        # Calculate total points safely
        try:
            total_points = db.session.query(func.coalesce(func.sum(UserChallenge.awarded_points), 0))\
                .filter_by(user_id=current_user.id, status='completed')\
                .scalar()
        except Exception as e:
            app.logger.error(f"Error calculating total points: {str(e)}")
            total_points = 0
        
        return render_template('gamification/conservation_challenges.html',
                            beginner_challenges=beginner_challenges,
                            intermediate_challenges=intermediate_challenges,
                            advanced_challenges=advanced_challenges,
                            user_challenges=user_challenges,
                            completed_challenges=completed_challenges,
                            total_points=total_points)
    except Exception as e:
        app.logger.error(f"Error in conservation_challenges: {str(e)}")
        flash('An error occurred while loading challenges. Please try again.', 'error')
        return redirect(url_for('main.index'))

@gamification.route('/start-conservation-challenge/<int:challenge_id>')
@login_required
def start_conservation_challenge(challenge_id):
    """Start a new conservation challenge"""
    challenge = ConservationChallenge.query.get_or_404(challenge_id)

    # Check if user already has this challenge
    existing_challenge = UserChallenge.query\
        .filter_by(
            user_id=current_user.id,
            conservation_challenge_id=challenge_id,
            status='in_progress'
        ).first()

    if existing_challenge:
        flash('You already have this challenge in progress!', 'warning')
        return redirect(url_for('gamification.conservation_challenges'))

    # Check active challenges limit
    active_challenges = UserChallenge.query\
        .filter_by(
            user_id=current_user.id,
            status='in_progress'
        ).count()

    if active_challenges >= 3:
        flash('You can only have 3 active challenges at a time. Complete or abandon some challenges first.', 'warning')
        return redirect(url_for('gamification.conservation_challenges'))

    try:
        # Create new challenge
        user_challenge = UserChallenge(
            user_id=current_user.id,
            conservation_challenge_id=challenge_id,
            status='in_progress',
            progress_data=json.dumps({
                'started': True,
                'steps_completed': [],
                'last_updated': datetime.utcnow().isoformat()
            })
        )
        db.session.add(user_challenge)
        db.session.commit()

        flash(f'Started challenge: {challenge.title}', 'success')
        return redirect(url_for('gamification.view_challenge', challenge_id=user_challenge.id))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error starting challenge: {str(e)}")
        flash('An error occurred while starting the challenge. Please try again.', 'error')
        return redirect(url_for('gamification.conservation_challenges'))

@gamification.route('/view-challenge/<int:challenge_id>')
@login_required
def view_challenge(challenge_id):
    """View challenge details and progress"""
    user_challenge = UserChallenge.query\
        .filter_by(id=challenge_id, user_id=current_user.id)\
        .first_or_404()
    
    challenge = user_challenge.conservation
    progress_data = json.loads(user_challenge.progress_data)
    requirements = json.loads(challenge.requirements) if challenge.requirements else []
    
    completed_steps = progress_data.get('steps_completed', [])
    completion_percentage = (len(completed_steps) / len(requirements)) * 100 if requirements else 0
    
    return render_template('gamification/view_challenge.html',
                         user_challenge=user_challenge,
                         challenge=challenge,
                         progress_data=progress_data,
                         requirements=requirements,
                         completion_percentage=completion_percentage)

@gamification.route('/update-challenge-progress/<int:challenge_id>', methods=['POST'])
@login_required
def update_challenge_progress(challenge_id):
    """Update progress on a conservation challenge"""
    user_challenge = UserChallenge.query\
        .filter_by(id=challenge_id, user_id=current_user.id)\
        .first_or_404()
    
    if user_challenge.status != 'in_progress':
        flash('This challenge is no longer active.', 'warning')
        return redirect(url_for('gamification.conservation_challenges'))
    
    challenge = user_challenge.conservation
    progress_data = json.loads(user_challenge.progress_data)
    completed_steps = set(progress_data.get('steps_completed', []))
    
    # Update completed steps
    step_id = request.form.get('step_id')
    if step_id:
        completed_steps.add(step_id)
        progress_data['steps_completed'] = list(completed_steps)
        progress_data['last_updated'] = datetime.utcnow().isoformat()
        user_challenge.progress_data = json.dumps(progress_data)
    
    # Check if challenge is completed
    requirements = json.loads(challenge.requirements) if challenge.requirements else []
    if len(completed_steps) >= len(requirements):
        user_challenge.status = 'completed'
        user_challenge.completed_at = datetime.utcnow()
        user_challenge.awarded_points = challenge.points
        
        # Update user points
        current_user.points = (current_user.points or 0) + challenge.points
        
        flash(f'Challenge completed! You earned {challenge.points} points!', 'success')
        
        # Check for achievements
        num_achievements = check_and_award_achievement(
            current_user.id,
            'conservation',
            challenge.points
        )
        if num_achievements > 0:
            flash(f'You unlocked {num_achievements} new achievement(s)!', 'success')
    
    db.session.commit()
    return redirect(url_for('gamification.view_challenge', challenge_id=challenge_id))

@gamification.route('/abandon-challenge/<int:challenge_id>')
@login_required
def abandon_challenge(challenge_id):
    """Abandon a conservation challenge"""
    user_challenge = UserChallenge.query\
        .filter_by(id=challenge_id, user_id=current_user.id, status='in_progress')\
        .first_or_404()
    
    user_challenge.status = 'abandoned'
    db.session.commit()
    
    flash('Challenge abandoned. You can start a new one!', 'info')
    return redirect(url_for('gamification.conservation_challenges'))

@gamification.route('/achievements')
@login_required
def achievements_dashboard():
    """Display user achievements and progress"""
    # Get user's achievements with their levels
    achievements = Achievement.query\
        .join(AchievementLevel)\
        .filter(Achievement.user_id == current_user.id)\
        .all()
    
    # Calculate overall progress
    total_points = sum(achievement.points for achievement in achievements)
    
    # Get next available achievements
    available_levels = AchievementLevel.query\
        .filter(~AchievementLevel.achievement_id.in_(
            Achievement.query.with_entities(Achievement.id)\
            .filter_by(user_id=current_user.id)
        ))\
        .order_by(AchievementLevel.points_required)\
        .limit(3)\
        .all()
    
    return render_template('gamification/achievements.html',
                         achievements=achievements,
                         total_points=total_points,
                         available_levels=available_levels)

@gamification.route('/api/achievements/progress')
@login_required
def achievement_progress():
    """Get achievement progress data for visualization"""
    try:
        achievements = Achievement.query\
            .filter_by(user_id=current_user.id)\
            .all()
        
        # Group achievements by category
        categories = {}
        for achievement in achievements:
            if achievement.category not in categories:
                categories[achievement.category] = {
                    'completed': 0,
                    'points': 0,
                    'achievements': []
                }
            categories[achievement.category]['completed'] += 1
            categories[achievement.category]['points'] += achievement.points
            categories[achievement.category]['achievements'].append({
                'title': achievement.title,
                'description': achievement.description,
                'points': achievement.points,
                'badge_image': achievement.badge_image,
                'achieved_at': achievement.achieved_at.strftime('%Y-%m-%d')
            })
        
        return jsonify({
            'categories': categories,
            'total_points': sum(cat['points'] for cat in categories.values()),
            'total_achievements': sum(cat['completed'] for cat in categories.values())
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_and_award_achievement(user_id, category, action_points):
    """Check if user qualifies for new achievements and award them"""
    try:
        # Get the user's current points in this category
        current_points = db.session.query(
            func.sum(Achievement.points)
        ).filter_by(
            user_id=user_id,
            category=category
        ).scalar() or 0
        
        # Add new action points
        total_points = current_points + action_points
        
        # Find eligible achievement levels
        eligible_levels = AchievementLevel.query\
            .filter(
                AchievementLevel.points_required <= total_points,
                ~AchievementLevel.id.in_(
                    Achievement.query.with_entities(Achievement.id)\
                    .filter_by(user_id=user_id)
                )
            ).all()
        
        # Award new achievements
        for level in eligible_levels:
            achievement = Achievement(
                user_id=user_id,
                title=level.name,
                description=level.description,
                badge_image=level.badge_image,
                category=category,
                points=level.points_required,
                achieved_at=datetime.utcnow()
            )
            db.session.add(achievement)
            flash(f'New Achievement Unlocked: {level.name}!', 'success')
        
        if eligible_levels:
            db.session.commit()
        
        return len(eligible_levels)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in check_and_award_achievement: {str(e)}")
        return 0

from flask import Flask
app = Flask(__name__)