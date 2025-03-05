from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import ForumCategory, ForumThread, ForumPost
from forms import ThreadForm, PostForm, CategoryForm

forum = Blueprint('forum', __name__)

@forum.route('/forum')
@login_required
def index():
    categories = ForumCategory.query.all()
    form = CategoryForm() if current_user.role == 'teacher' else None
    return render_template('forum/index.html', categories=categories, form=form)

@forum.route('/forum/category/create', methods=['POST'])
@login_required
def create_category():
    if current_user.role != 'teacher':
        flash('Only teachers can create categories.', 'danger')
        return redirect(url_for('forum.index'))

    form = CategoryForm()
    if form.validate_on_submit():
        category = ForumCategory(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully!', 'success')
    return redirect(url_for('forum.index'))

@forum.route('/forum/category/<int:id>')
@login_required
def view_category(id):
    category = ForumCategory.query.get_or_404(id)
    threads = ForumThread.query.filter_by(category_id=id)\
        .order_by(ForumThread.is_pinned.desc(), ForumThread.created_at.desc()).all()
    return render_template('forum/category.html', category=category, threads=threads)

@forum.route('/forum/thread/new/<int:category_id>', methods=['GET', 'POST'])
@login_required
def create_thread(category_id):
    category = ForumCategory.query.get_or_404(category_id)
    form = ThreadForm()

    if form.validate_on_submit():
        thread = ForumThread(
            title=form.title.data,
            content=form.content.data,
            author_id=current_user.id,
            category_id=category_id
        )
        db.session.add(thread)
        db.session.commit()
        flash('Thread created successfully!', 'success')
        return redirect(url_for('forum.view_thread', id=thread.id))

    return render_template('forum/create_thread.html', form=form, category=category)

@forum.route('/forum/thread/<int:id>')
@login_required
def view_thread(id):
    thread = ForumThread.query.get_or_404(id)
    # Increment view count
    thread.view_count += 1
    db.session.commit()

    posts = ForumPost.query.filter_by(thread_id=id)\
        .order_by(ForumPost.created_at).all()
    form = PostForm()
    return render_template('forum/view_thread.html', thread=thread, posts=posts, form=form)

@forum.route('/forum/thread/<int:id>/reply', methods=['POST'])
@login_required
def reply_thread(id):
    thread = ForumThread.query.get_or_404(id)
    if thread.is_locked and current_user.role != 'teacher':
        flash('This thread is locked.', 'warning')
        return redirect(url_for('forum.view_thread', id=id))

    form = PostForm()
    if form.validate_on_submit():
        post = ForumPost(
            content=form.content.data,
            author_id=current_user.id,
            thread_id=id
        )
        db.session.add(post)
        db.session.commit()
        flash('Reply posted successfully!', 'success')

    return redirect(url_for('forum.view_thread', id=id))

@forum.route('/forum/thread/<int:id>/toggle_pin', methods=['POST'])
@login_required
def toggle_pin_thread(id):
    if current_user.role != 'teacher':
        flash('Only teachers can pin/unpin threads.', 'danger')
        return redirect(url_for('forum.view_thread', id=id))

    thread = ForumThread.query.get_or_404(id)
    thread.is_pinned = not thread.is_pinned
    db.session.commit()
    flash(f'Thread {"pinned" if thread.is_pinned else "unpinned"} successfully!', 'success')
    return redirect(url_for('forum.view_thread', id=id))

@forum.route('/forum/thread/<int:id>/toggle_lock', methods=['POST'])
@login_required
def toggle_lock_thread(id):
    if current_user.role != 'teacher':
        flash('Only teachers can lock/unlock threads.', 'danger')
        return redirect(url_for('forum.view_thread', id=id))

    thread = ForumThread.query.get_or_404(id)
    thread.is_locked = not thread.is_locked
    db.session.commit()
    flash(f'Thread {"locked" if thread.is_locked else "unlocked"} successfully!', 'success')
    return redirect(url_for('forum.view_thread', id=id))