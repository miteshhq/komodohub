from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, FileField, FloatField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Optional
from models import SchoolAccessCode, User
from datetime import datetime

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    role = SelectField('Role', choices=[
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('community', 'Community Member')
    ])
    access_code = StringField('School Access Code', 
        description='Required for student registration. Get this code from your teacher.')

    def validate_access_code(self, field):
        if self.role.data == 'student':
            if not field.data:
                raise ValidationError('Access code is required for student registration')

            code = SchoolAccessCode.query.filter_by(code=field.data.upper()).first()
            if not code:
                raise ValidationError('Invalid access code')
            if not code.is_valid:
                raise ValidationError('This access code has expired or reached its usage limit')

class AccessCodeForm(FlaskForm):
    max_uses = SelectField('Maximum Uses', 
        choices=[(30, '30'), (50, '50'), (100, '100'), (0, 'Unlimited')],
        coerce=int,
        default=30)
    valid_days = SelectField('Valid For',
        choices=[(7, '1 Week'), (30, '1 Month'), (90, '3 Months'), (180, '6 Months')],
        coerce=int,
        default=30)
    description = StringField('Description', 
        validators=[Length(max=200)],
        description='Optional: Add a note to help you identify this code later')

class SpeciesForm(FlaskForm):
    name = StringField('Species Name', validators=[DataRequired()])
    scientific_name = StringField('Scientific Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    population = StringField('Population Estimate')
    conservation_status = StringField('Conservation Status')
    habitat = StringField('Habitat')
    threats = TextAreaField('Threats')

class ResourceForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])

class ProgramForm(FlaskForm):
    title = StringField('Program Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])

class SightingForm(FlaskForm):
    species_id = SelectField('Species', coerce=int, validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    latitude = FloatField('Latitude', validators=[Optional()],
        description='Optional: Automatically filled if you use the location picker')
    longitude = FloatField('Longitude', validators=[Optional()],
        description='Optional: Automatically filled if you use the location picker')
    description = TextAreaField('Description', validators=[DataRequired()])
    sighting_date = DateField('Sighting Date', validators=[DataRequired()], default=datetime.utcnow)
    photos = FileField('Photos', description='Optional: Add photos of the sighting')
    habitat_notes = TextAreaField('Habitat Notes', validators=[Optional()],
        description='Optional: Describe the surrounding environment')
    behavior_notes = TextAreaField('Behavior Notes', validators=[Optional()],
        description='Optional: Describe any notable behaviors observed')

class LibraryResourceForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    resource_type = SelectField('Type', choices=[
        ('report', 'Report'),
        ('essay', 'Essay'),
        ('article', 'Article')
    ], validators=[DataRequired()])
    is_public = SelectField('Visibility', choices=[
        ('true', 'Public - Visible to everyone'),
        ('false', 'Private - Visible only to your organization')
    ], validators=[DataRequired()])

class MessageForm(FlaskForm):
    recipient_id = SelectField('To', coerce=int, validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Message', validators=[DataRequired()])

class NoteForm(FlaskForm):
    content = TextAreaField('Feedback', validators=[DataRequired()])

class ProfileCustomizationForm(FlaskForm):
    theme_preference = SelectField('Theme', choices=[
        ('light', 'Light Theme'),
        ('dark', 'Dark Theme'),
        ('nature', 'Nature Theme')
    ], validators=[DataRequired()])
    avatar = FileField('Avatar Image')

class GameChallengeForm(FlaskForm):
    title = StringField('Challenge Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    points = SelectField('Points', choices=[(str(i*10), str(i*10)) for i in range(1, 11)], validators=[DataRequired()])
    difficulty = SelectField('Difficulty', choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ], validators=[DataRequired()])
    challenge_type = SelectField('Challenge Type', choices=[
        ('quiz', 'Quiz'),
        ('identification', 'Species Identification'),
        ('conservation_task', 'Conservation Task')
    ], validators=[DataRequired()])

class ThreadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])

class PostForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])