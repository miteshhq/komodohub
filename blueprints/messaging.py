from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import Message, Note, User
from forms import MessageForm, NoteForm

messaging = Blueprint('messaging', __name__)

@messaging.route('/messages')
@messaging.route('/inbox')  # Added route alias for inbox
@login_required
def inbox():  # Renamed from message_list to inbox
    # Get root messages (messages without a parent)
    received = Message.query.filter_by(
        recipient_id=current_user.id,
        parent_id=None
    ).order_by(Message.created_at.desc()).all()

    sent = Message.query.filter_by(
        sender_id=current_user.id,
        parent_id=None
    ).order_by(Message.created_at.desc()).all()

    return render_template('messaging/list.html', received=received, sent=sent)

@messaging.route('/messages/new', methods=['GET', 'POST'])
@login_required
def send_message():
    form = MessageForm()
    # Only allow messaging students if teacher, or teachers if student
    if current_user.role == 'teacher':
        form.recipient_id.choices = [(u.id, u.username) for u in User.query.filter_by(role='student').all()]
    elif current_user.role == 'student':
        form.recipient_id.choices = [(u.id, u.username) for u in User.query.filter_by(role='teacher').all()]

    if form.validate_on_submit():
        message = Message(
            sender_id=current_user.id,
            recipient_id=form.recipient_id.data,
            subject=form.subject.data,
            content=form.content.data
        )
        db.session.add(message)
        db.session.commit()
        flash('Message sent successfully!', 'success')
        return redirect(url_for('messaging.inbox'))

    return render_template('messaging/new.html', form=form)

@messaging.route('/messages/<int:id>')
@login_required
def view_message(id):
    message = Message.query.get_or_404(id)
    if message.recipient_id == current_user.id:
        if not message.read:
            message.read = True
            db.session.commit()
    elif message.sender_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('messaging.inbox'))

    # Get all messages in the thread
    thread = message.get_thread()
    return render_template('messaging/view.html', message=message, thread=thread)

@messaging.route('/messages/reply/<int:parent_id>', methods=['POST'])
@login_required
def reply_message(parent_id):
    parent = Message.query.get_or_404(parent_id)
    if parent.recipient_id != current_user.id and parent.sender_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('messaging.inbox'))

    content = request.form.get('content')
    if not content:
        flash('Reply cannot be empty.', 'danger')
        return redirect(url_for('messaging.view_message', id=parent_id))

    reply = Message(
        sender_id=current_user.id,
        recipient_id=parent.sender_id if parent.recipient_id == current_user.id else parent.recipient_id,
        parent_id=parent_id,
        subject=f"Re: {parent.subject}" if parent.subject else None,
        content=content
    )
    db.session.add(reply)
    db.session.commit()
    flash('Reply sent successfully!', 'success')
    return redirect(url_for('messaging.view_message', id=parent_id))

@messaging.route('/notes/add/<string:resource_type>/<int:resource_id>/<int:student_id>', methods=['POST'])
@login_required
def add_note(resource_type, resource_id, student_id):
    if current_user.role != 'teacher':
        flash('Only teachers can add notes.', 'danger')
        return redirect(url_for('main.dashboard'))

    form = NoteForm()
    if form.validate_on_submit():
        note = Note(
            content=form.content.data,
            teacher_id=current_user.id,
            student_id=student_id,
            resource_type=resource_type,
            resource_id=resource_id
        )
        db.session.add(note)
        db.session.commit()
        flash('Note added successfully!', 'success')

    return redirect(request.referrer or url_for('main.dashboard'))