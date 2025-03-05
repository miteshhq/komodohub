from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from forms import ProfileCustomizationForm
from models import Achievement
import os

profile = Blueprint('profile', __name__)

@profile.route('/profile/customize', methods=['GET', 'POST'])
@login_required
def customize():
    form = ProfileCustomizationForm()
    if form.validate_on_submit():
        if form.avatar.data:
            # Save avatar image
            filename = f'avatar_{current_user.id}.svg'
            form.avatar.data.save(os.path.join('static', 'avatars', filename))
            current_user.avatar = filename
        
        current_user.theme_preference = form.theme_preference.data
        db.session.commit()
        flash('Profile customization saved!', 'success')
        return redirect(url_for('profile.view_achievements'))
    
    return render_template('profile/customize.html', form=form)

@profile.route('/profile/achievements')
@login_required
def view_achievements():
    achievements = Achievement.query.filter_by(user_id=current_user.id).all()
    return render_template('profile/achievements.html', achievements=achievements)
