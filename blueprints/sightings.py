from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import Species, SpeciesSighting, Achievement
from forms import SightingForm
import logging
from datetime import datetime

sightings = Blueprint('sightings', __name__)

@sightings.route('/sightings')
@login_required
def list_sightings():
    if current_user.role == 'teacher':
        # Teachers can see all sightings
        sightings = SpeciesSighting.query.order_by(SpeciesSighting.created_at.desc()).all()
    else:
        # Students and community members see only their own sightings
        sightings = SpeciesSighting.query.filter_by(user_id=current_user.id)\
            .order_by(SpeciesSighting.created_at.desc()).all()
    return render_template('sightings/list.html', sightings=sightings)

@sightings.route('/sightings/report', methods=['GET', 'POST'])
@login_required
def report_sighting():
    form = SightingForm()
    form.species_id.choices = [(s.id, s.name) for s in Species.query.all()]

    if form.validate_on_submit():
        sighting = SpeciesSighting(
            species_id=form.species_id.data,
            user_id=current_user.id,
            location=form.location.data,
            description=form.description.data,
            sighting_date=form.sighting_date.data,
            status='pending'  # Set initial status as pending
        )
        db.session.add(sighting)
        db.session.commit()
        logging.info(f'New sighting reported by {current_user.username} for species ID: {form.species_id.data}')
        flash('Sighting reported successfully! Waiting for verification.', 'success')
        return redirect(url_for('sightings.list_sightings'))

    return render_template('sightings/report.html', form=form)

@sightings.route('/sightings/<int:id>')
@login_required
def view_sighting(id):
    sighting = SpeciesSighting.query.get_or_404(id)
    return render_template('sightings/view.html', sighting=sighting)

@sightings.route('/sightings/verify/<int:id>', methods=['POST'])
@login_required
def verify_sighting(id):
    if current_user.role != 'teacher':
        flash('Only teachers can verify sightings.', 'danger')
        return redirect(url_for('sightings.list_sightings'))

    sighting = SpeciesSighting.query.get_or_404(id)
    action = request.form.get('action')

    if action == 'verify':
        sighting.status = 'verified'
        flash('Sighting verified successfully!', 'success')

        # Check if user deserves an achievement
        verified_count = SpeciesSighting.query.filter_by(
            user_id=sighting.user_id,
            status='verified'
        ).count()

        # Achievement thresholds
        if verified_count == 1:
            achievement = Achievement(
                user_id=sighting.user_id,
                title="First Sighting",
                description="Successfully reported your first verified species sighting!",
                badge_image="badges/first_sighting.svg",
                category="sightings",
                points=50
            )
            db.session.add(achievement)
        elif verified_count == 5:
            achievement = Achievement(
                user_id=sighting.user_id,
                title="Expert Observer",
                description="Got 5 species sightings verified!",
                badge_image="badges/expert_observer.svg",
                category="sightings",
                points=100
            )
            db.session.add(achievement)
        elif verified_count == 10:
            achievement = Achievement(
                user_id=sighting.user_id,
                title="Master Naturalist",
                description="Achieved 10 verified species sightings!",
                badge_image="badges/master_naturalist.svg",
                category="sightings",
                points=200
            )
            db.session.add(achievement)

    elif action == 'reject':
        sighting.status = 'rejected'
        flash('Sighting rejected.', 'warning')

    db.session.commit()
    logging.info(f'Sighting {id} {action}d by teacher {current_user.username}')
    return redirect(url_for('sightings.view_sighting', id=id))