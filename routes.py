from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Species, EducationalResource, ConservationProgram
from forms import LoginForm, RegistrationForm, SpeciesForm, ResourceForm, ProgramForm

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Dashboard routes
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'teacher':
        return render_template('dashboard/teacher.html')
    elif current_user.role == 'student':
        return render_template('dashboard/student.html')
    else:
        return render_template('dashboard/community.html')

# Species routes
@app.route('/species')
def species_list():
    species = Species.query.all()
    return render_template('species/list.html', species=species)

@app.route('/species/add', methods=['GET', 'POST'])
@login_required
def add_species():
    if current_user.role != 'teacher':
        flash('Access denied', 'danger')
        return redirect(url_for('species_list'))
    
    form = SpeciesForm()
    if form.validate_on_submit():
        species = Species(
            name=form.name.data,
            scientific_name=form.scientific_name.data,
            description=form.description.data,
            population=form.population.data,
            conservation_status=form.conservation_status.data,
            habitat=form.habitat.data,
            threats=form.threats.data
        )
        db.session.add(species)
        db.session.commit()
        flash('Species added successfully!', 'success')
        return redirect(url_for('species_list'))
    return render_template('species/add.html', form=form)

# Education routes
@app.route('/education')
def education_resources():
    resources = EducationalResource.query.all()
    return render_template('education/resources.html', resources=resources)

# Programs routes
@app.route('/programs')
def programs():
    programs = ConservationProgram.query.all()
    return render_template('programs/index.html', programs=programs)
