from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import Species, UserProgress, SpeciesSighting
from forms import SpeciesForm
from datetime import datetime, timedelta
from sqlalchemy import desc, asc

species = Blueprint('species', __name__)

@species.route('/species')
def list():
    species_list = Species.query.all()

    # Track progress for students
    if current_user.is_authenticated and current_user.role == 'student':
        for s in species_list:
            # Check if progress already exists
            progress = UserProgress.query.filter_by(
                user_id=current_user.id,
                content_type='species',
                content_id=s.id
            ).first()

            if not progress:
                progress = UserProgress(
                    user_id=current_user.id,
                    content_type='species',
                    content_id=s.id,
                    completed=True
                )
                db.session.add(progress)
        db.session.commit()

    return render_template('species/list.html', 
                         species=species_list,
                         datetime=datetime)

@species.route('/my-sightings')
@login_required
def my_sightings():
    sightings = SpeciesSighting.query.filter_by(user_id=current_user.id)\
        .order_by(SpeciesSighting.created_at.desc()).all()
    return render_template('species/my_sightings.html', sightings=sightings)

@species.route('/all-sightings')
@login_required
def all_sightings():
    if current_user.role not in ['teacher', 'community']:
        flash('Access denied. Only teachers and community members can view all sightings.', 'danger')
        return redirect(url_for('species.list'))

    # Get filter parameters
    role = request.args.get('role')
    date_range = request.args.get('date_range')
    sort = request.args.get('sort', 'date_desc')

    # Base query
    query = SpeciesSighting.query

    # Apply role filter
    if role:
        query = query.join(SpeciesSighting.observer).filter_by(role=role)

    # Apply date filter
    if date_range:
        if date_range == 'today':
            query = query.filter(SpeciesSighting.sighting_date >= datetime.today().date())
        elif date_range == 'week':
            query = query.filter(SpeciesSighting.sighting_date >= datetime.today() - timedelta(days=7))
        elif date_range == 'month':
            query = query.filter(SpeciesSighting.sighting_date >= datetime.today() - timedelta(days=30))

    # Apply sorting
    if sort == 'date_desc':
        query = query.order_by(desc(SpeciesSighting.sighting_date))
    elif sort == 'date_asc':
        query = query.order_by(asc(SpeciesSighting.sighting_date))
    elif sort == 'species':
        query = query.join(Species).order_by(Species.name)

    sightings = query.all()

    return render_template('species/all_sightings.html', 
                         sightings=sightings,
                         request=request)

@species.route('/species/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role != 'teacher':
        flash('Access denied', 'danger')
        return redirect(url_for('species.list'))

    form = SpeciesForm()
    if form.validate_on_submit():
        species = Species(
            name=form.name.data,
            scientific_name=form.scientific_name.data,
            description=form.description.data,
            population=form.population.data,
            conservation_status=form.conservation_status.data,
            habitat=form.habitat.data,
            threats=form.threats.data,
            created_by_id=current_user.id
        )
        db.session.add(species)
        db.session.commit()
        flash('Species added successfully!', 'success')
        return redirect(url_for('species.list'))
    return render_template('species/add.html', form=form)

@species.route('/species/<int:species_id>/report-sighting', methods=['POST'])
@login_required
def report_sighting(species_id):
    species = Species.query.get_or_404(species_id)

    # Get form data
    location = request.form.get('location')
    sighting_date = request.form.get('sighting_date')
    description = request.form.get('description')

    if not location or not sighting_date:
        flash('Please fill in all required fields', 'danger')
        return redirect(url_for('species.list'))

    try:
        sighting_date = datetime.strptime(sighting_date, '%Y-%m-%d')

        sighting = SpeciesSighting(
            species_id=species.id,
            user_id=current_user.id,
            location=location,
            sighting_date=sighting_date,
            description=description
        )

        db.session.add(sighting)
        db.session.commit()

        flash('Sighting reported successfully! It will be reviewed by our team.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error reporting sighting. Please try again.', 'danger')

    return redirect(url_for('species.list'))

@species.route('/sighting/<int:sighting_id>/update-status', methods=['POST'])
@login_required
def update_sighting_status(sighting_id):
    if current_user.role != 'teacher':
        flash('Only teachers can verify sightings.', 'danger')
        return redirect(url_for('species.all_sightings'))

    sighting = SpeciesSighting.query.get_or_404(sighting_id)
    new_status = request.form.get('status')

    if new_status in ['verified', 'rejected']:
        sighting.status = new_status
        db.session.commit()
        flash(f'Sighting status updated to {new_status}.', 'success')
    else:
        flash('Invalid status value.', 'danger')

    return redirect(url_for('species.all_sightings'))