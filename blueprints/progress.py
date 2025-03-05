from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import User, UserProgress, EducationalResource, Species, ConservationProgram

progress = Blueprint('progress', __name__)

@progress.route('/student-list')
@login_required
def student_list():
    if current_user.role != 'teacher':
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('main.dashboard'))

    students = User.query.filter_by(role='student').all()
    return render_template('progress/student_list.html', students=students)

@progress.route('/student-progress/<int:student_id>')
@login_required
def view_progress(student_id):
    # For students, only show their own progress
    if current_user.role == 'student' and current_user.id != student_id:
        flash('Access denied. You can only view your own progress.', 'danger')
        return redirect(url_for('main.dashboard'))

    # For teachers, allow viewing any student's progress
    if current_user.role != 'teacher' and current_user.id != student_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))

    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        flash('Invalid student ID.', 'danger')
        return redirect(url_for('progress.student_list'))

    progress_data = UserProgress.query.filter_by(user_id=student_id).all()

    # Get all available content
    resources = EducationalResource.query.all()
    species = Species.query.all()
    programs = ConservationProgram.query.all()

    return render_template('progress/view_progress.html',
                         student=student,
                         progress_data=progress_data,
                         resources=resources,
                         species=species,
                         programs=programs)

@progress.route('/update-progress/<int:student_id>', methods=['POST'])
@login_required
def update_progress(student_id):
    if current_user.role != 'teacher' and current_user.id != student_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))

    content_type = request.form.get('content_type')
    content_id = request.form.get('content_id')
    completed = request.form.get('completed') == 'true'

    progress = UserProgress.query.filter_by(
        user_id=student_id,
        content_type=content_type,
        content_id=content_id
    ).first()

    if not progress:
        progress = UserProgress(
            user_id=student_id,
            content_type=content_type,
            content_id=content_id
        )
        db.session.add(progress)

    progress.completed = completed
    db.session.commit()

    flash('Progress updated successfully!', 'success')
    return redirect(url_for('progress.view_progress', student_id=student_id))