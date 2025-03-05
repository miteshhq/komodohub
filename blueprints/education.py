from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import EducationalResource, UserProgress, ResourceTag
from forms import ResourceForm

education = Blueprint('education', __name__)

@education.route('/education')
def resources():
    # Get filter parameters
    tag_filter = request.args.get('tag')
    search_query = request.args.get('search')

    # Base query
    query = EducationalResource.query

    # Apply filters
    if tag_filter:
        query = query.join(EducationalResource.tags).filter(ResourceTag.name == tag_filter)
    if search_query:
        query = query.filter(EducationalResource.title.ilike(f'%{search_query}%'))

    # Get all available tags for the filter dropdown
    tags = ResourceTag.query.all()

    # Execute query with filters
    resources = query.order_by(EducationalResource.created_at.desc()).all()

    form = ResourceForm()  # Create form instance for the modal

    # Track progress for students
    if current_user.is_authenticated and current_user.role == 'student':
        for resource in resources:
            # Check if progress already exists
            progress = UserProgress.query.filter_by(
                user_id=current_user.id,
                content_type='resource',
                content_id=resource.id
            ).first()

            if not progress:
                progress = UserProgress(
                    user_id=current_user.id,
                    content_type='resource',
                    content_id=resource.id,
                    completed=True
                )
                db.session.add(progress)
        db.session.commit()

    return render_template('education/resources.html', 
                         resources=resources, 
                         form=form, 
                         tags=tags,
                         current_tag=tag_filter,
                         search_query=search_query)

@education.route('/education/add', methods=['GET', 'POST'])
@login_required
def add_resource():
    if current_user.role != 'teacher':
        flash('Access denied', 'danger')
        return redirect(url_for('education.resources'))

    form = ResourceForm()
    if form.validate_on_submit():
        resource = EducationalResource(
            title=form.title.data,
            content=form.content.data,
            author_id=current_user.id
        )
        db.session.add(resource)
        db.session.commit()
        flash('Resource added successfully!', 'success')
        return redirect(url_for('education.resources'))
    return render_template('education/add.html', form=form)