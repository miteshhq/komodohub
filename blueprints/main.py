from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Species, EducationalResource, ConservationProgram

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'teacher':
        species = Species.query.all()
        resources = EducationalResource.query.all()
        programs = ConservationProgram.query.all()
        return render_template('dashboard/teacher.html', 
                             species=species, 
                             resources=resources, 
                             programs=programs)
    elif current_user.role == 'student':
        featured_species = Species.query.limit(5).all()  # Get first 5 species for featured section
        return render_template('dashboard/student.html', 
                             featured_species=featured_species)
    else:  # community member
        active_programs = ConservationProgram.query.all()
        species_count = Species.query.count()
        user_contributions = ConservationProgram.query.filter_by(coordinator_id=current_user.id).count()
        return render_template('dashboard/community.html',
                             active_programs=active_programs,
                             species_count=species_count,
                             user_contributions=user_contributions)