from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import SchoolAccessCode, User
from forms import AccessCodeForm
from datetime import datetime

school = Blueprint('school', __name__)

@school.route('/school/access-codes')
@login_required
def list_access_codes():
    if not current_user.can_generate_access_codes():
        flash('Access denied. Only teachers can manage access codes.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    active_codes = SchoolAccessCode.query.filter_by(
        school_id=current_user.id,
        is_active=True
    ).order_by(SchoolAccessCode.created_at.desc()).all()
    
    expired_codes = SchoolAccessCode.query.filter_by(
        school_id=current_user.id,
        is_active=False
    ).order_by(SchoolAccessCode.created_at.desc()).all()
    
    return render_template('school/access_codes.html',
                         active_codes=active_codes,
                         expired_codes=expired_codes)

@school.route('/school/access-codes/generate', methods=['GET', 'POST'])
@login_required
def generate_access_code():
    if not current_user.can_generate_access_codes():
        flash('Access denied. Only teachers can generate access codes.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = AccessCodeForm()
    if form.validate_on_submit():
        try:
            code = current_user.generate_access_code(
                max_uses=form.max_uses.data,
                valid_days=form.valid_days.data,
                description=form.description.data
            )
            flash(f'New access code generated: {code.code}', 'success')
            return redirect(url_for('school.list_access_codes'))
        except Exception as e:
            flash(f'Error generating access code: {str(e)}', 'danger')
    
    return render_template('school/generate_code.html', form=form)

@school.route('/school/access-codes/<int:id>/deactivate', methods=['POST'])
@login_required
def deactivate_access_code(id):
    if not current_user.can_generate_access_codes():
        flash('Access denied. Only teachers can manage access codes.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    code = SchoolAccessCode.query.get_or_404(id)
    if code.school_id != current_user.id:
        flash('Access denied. You can only manage your own access codes.', 'danger')
        return redirect(url_for('school.list_access_codes'))
    
    code.is_active = False
    db.session.commit()
    flash('Access code deactivated successfully.', 'success')
    return redirect(url_for('school.list_access_codes'))
