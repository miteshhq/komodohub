from flask import Blueprint, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models import ConservationProgram, UserPrograms
from forms import ProgramForm
from datetime import datetime

programs = Blueprint('programs', __name__)

@programs.route('/programs')
def list():
    programs = ConservationProgram.query.order_by(ConservationProgram.start_date.desc()).all()
    form = ProgramForm()  # Create form instance for the modal
    return render_template('programs/index.html', programs=programs, form=form)

@programs.route('/programs/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role not in ['teacher', 'community']:
        flash('Access denied', 'danger')
        return redirect(url_for('programs.list'))

    form = ProgramForm()
    if form.validate_on_submit():
        program = ConservationProgram(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            coordinator_id=current_user.id
        )
        db.session.add(program)
        db.session.commit()
        flash('Program added successfully!', 'success')
        return redirect(url_for('programs.list'))
    return render_template('programs/add.html', form=form)

@programs.route('/programs/<int:program_id>/join', methods=['POST'])
@login_required
def join_program(program_id):
    program = ConservationProgram.query.get_or_404(program_id)

    # Check if user is already enrolled
    if program in current_user.programs_joined:
        flash('You are already enrolled in this program.', 'info')
        return redirect(url_for('programs.list'))

    # Create new enrollment
    enrollment = UserPrograms(
        user_id=current_user.id,
        program_id=program_id,
        status='active'
    )
    program.participant_count += 1

    db.session.add(enrollment)
    db.session.commit()

    flash('Successfully joined the program!', 'success')
    return redirect(url_for('programs.list'))

@programs.route('/programs/<int:program_id>/leave', methods=['POST'])
@login_required
def leave_program(program_id):
    program = ConservationProgram.query.get_or_404(program_id)

    # Check if user is actually enrolled in the program
    if program not in current_user.programs_joined:
        flash('You are not enrolled in this program.', 'warning')
        return redirect(url_for('programs.list'))

    try:
        # Remove the program from user's joined programs
        current_user.programs_joined.remove(program)
        # Update participant count
        program.participant_count = max(0, program.participant_count - 1)

        # Update the enrollment status
        enrollment = UserPrograms.query.filter_by(
            user_id=current_user.id,
            program_id=program_id
        ).first()
        if enrollment:
            enrollment.status = 'left'

        db.session.commit()
        flash('You have successfully left the program.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while leaving the program.', 'danger')

    return redirect(url_for('programs.list'))

@programs.route('/programs/my')
@login_required
def my_programs():
    # Get all active enrollments for the current user
    enrollments = UserPrograms.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).all()

    # Get the corresponding programs
    joined_programs = [
        ConservationProgram.query.get(enrollment.program_id)
        for enrollment in enrollments
    ]

    return render_template('programs/my_programs.html', programs=joined_programs)