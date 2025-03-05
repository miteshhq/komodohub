import secrets
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # 'species', 'resource', 'quiz', etc.
    content_id = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False)  # teacher, student, community
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    avatar = db.Column(db.String(200), default='default.svg')  # URL to avatar image
    theme_preference = db.Column(db.String(50), default='light')  # light, dark, nature
    achievements = db.relationship('Achievement', backref='user', lazy=True)

    # Relationships
    resources = db.relationship('EducationalResource', backref='author', lazy=True)
    programs = db.relationship('ConservationProgram', backref='coordinator', lazy=True)
    progress = db.relationship('UserProgress', backref='user', lazy=True)
    programs_joined = db.relationship('ConservationProgram', 
                                    secondary='user_programs',
                                    backref=db.backref('participants', lazy='dynamic'))
    species_sightings = db.relationship('SpeciesSighting', back_populates='observer', lazy=True)
    access_codes = db.relationship('SchoolAccessCode', backref='school', lazy=True)
    challenges = db.relationship('UserChallenge', back_populates='player', lazy=True)

    def set_password(self, password):
        if not password:
            raise ValueError('Password cannot be empty')
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_progress_percentage(self):
        if self.role != 'student':
            return 100

        total_items = (
            Species.query.count() +
            EducationalResource.query.count() +
            ConservationProgram.query.count()
        )

        if total_items == 0:
            return 0

        completed_items = UserProgress.query.filter_by(
            user_id=self.id,
            completed=True
        ).count()

        return int((completed_items / total_items) * 100)

    def can_generate_access_codes(self):
        """Check if user can generate school access codes"""
        return self.role == 'teacher'

    def generate_access_code(self, max_uses=30, valid_days=30, description=None):
        """Generate a new school access code"""
        if not self.can_generate_access_codes():
            raise ValueError("Only teachers can generate access codes")

        code = SchoolAccessCode(
            code=SchoolAccessCode.generate_code(),
            school_id=self.id,
            expires_at=datetime.utcnow() + timedelta(days=valid_days),
            max_uses=max_uses,
            description=description
        )
        db.session.add(code)
        db.session.commit()
        return code

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    badge_image = db.Column(db.String(200))  # URL to badge image
    achieved_at = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50))  # e.g., 'sightings', 'education', 'conservation'
    points = db.Column(db.Integer, default=0)


class AchievementLevel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    points_required = db.Column(db.Integer, nullable=False)
    badge_image = db.Column(db.String(200))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with Achievement
    achievement = db.relationship('Achievement', backref='levels')

class SpeciesIdentificationChallenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # easy, medium, hard
    question_text = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)
    wrong_options = db.Column(db.Text, nullable=False)  # JSON array of wrong answers
    hint = db.Column(db.Text)
    points = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship with Species
    species = db.relationship('Species', backref='identification_challenges')

class ConservationChallenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    challenge_type = db.Column(db.String(50), nullable=False)  # research, action, awareness
    difficulty = db.Column(db.String(20), nullable=False)  # easy, medium, hard
    points = db.Column(db.Integer, nullable=False)
    duration_days = db.Column(db.Integer, default=7)  # Duration to complete the challenge
    requirements = db.Column(db.Text)  # JSON string of completion requirements
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship
    participants = db.relationship('UserChallenge', back_populates='conservation')

class UserChallenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    conservation_challenge_id = db.Column(db.Integer, db.ForeignKey('conservation_challenge.id'))
    challenge_type = db.Column(db.String(20), default='conservation')
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, failed
    progress_data = db.Column(db.Text)  # JSON string of progress details
    score = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    awarded_points = db.Column(db.Integer)

    # Relationships
    player = db.relationship('User', back_populates='challenges')
    conservation = db.relationship('ConservationChallenge', back_populates='participants')

class UserSpeciesIdentification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('species_identification_challenge.id'), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    points_earned = db.Column(db.Integer)
    attempt_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='species_identifications')
    challenge = db.relationship('SpeciesIdentificationChallenge', backref='attempts')

class GameChallenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, default=0)
    difficulty = db.Column(db.String(20))  # easy, medium, hard
    challenge_type = db.Column(db.String(50))  # quiz, identification, conservation_task
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Species(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    scientific_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    population = db.Column(db.Integer)
    conservation_status = db.Column(db.String(50))
    habitat = db.Column(db.String(100))
    threats = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Relationships
    sightings = db.relationship('SpeciesSighting', back_populates='species', lazy=True)
    created_by = db.relationship('User', backref='species_created', foreign_keys=[created_by_id])
    population_records = db.relationship('PopulationRecord', back_populates='species', lazy=True)
    habitats = db.relationship('HabitatData', back_populates='species', lazy=True)
    migrations = db.relationship('MigrationPattern', back_populates='species', lazy=True)

class ResourceTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

resource_tags = db.Table('resource_tags',
    db.Column('resource_id', db.Integer, db.ForeignKey('educational_resource.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('resource_tag.id'), primary_key=True)
)

class EducationalResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.relationship('ResourceTag', secondary=resource_tags, backref='resources')

class ConservationProgram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    coordinator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    participant_count = db.Column(db.Integer, default=0)

class UserPrograms(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('conservation_program.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, completed, left

class LibraryResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # 'report', 'essay', 'article'
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # If associated with a school
    community_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # If associated with a community
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=True)

    # Relationships
    author = db.relationship('User', foreign_keys=[author_id], backref='resources_authored')
    school = db.relationship('User', foreign_keys=[school_id], backref='school_resources')
    community = db.relationship('User', foreign_keys=[community_id], backref='community_resources')

class SpeciesSighting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sighting_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    species = db.relationship('Species', back_populates='sightings')
    observer = db.relationship('User', back_populates='species_sightings')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('message.id'))  # For message threading
    subject = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')
    replies = db.relationship('Message', backref=db.backref('parent', remote_side=[id]))

    def get_thread(self):
        """Get all messages in the same thread"""
        if self.parent_id:
            return self.parent.get_thread()
        return [self] + [reply for reply in self.replies]

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resource_type = db.Column(db.String(50))  # 'library_resource', 'species_sighting', etc.
    resource_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='notes_given')
    student = db.relationship('User', foreign_keys=[student_id], backref='notes_received')

class ForumCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    threads = db.relationship('ForumThread', backref='category', lazy=True)

class ForumThread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('forum_category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)

    # Relationships
    posts = db.relationship('ForumPost', backref='thread', lazy=True)
    author = db.relationship('User', backref='forum_threads')

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('forum_thread.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_solution = db.Column(db.Boolean, default=False)  # For marking helpful answers

    # Relationships
    author = db.relationship('User', backref='forum_posts')

class SchoolAccessCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), unique=True, nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    max_uses = db.Column(db.Integer, default=30)  # Default limit of 30 uses
    times_used = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.String(200))  # For teachers to identify different codes

    @staticmethod
    def generate_code():
        """Generate a unique 8-character access code"""
        while True:
            code = secrets.token_urlsafe(6)[:8].upper()
            if not SchoolAccessCode.query.filter_by(code=code).first():
                return code

    @property
    def is_valid(self):
        """Check if the code is still valid"""
        return (
            self.is_active and
            self.expires_at > datetime.utcnow() and
            (self.max_uses == 0 or self.times_used < self.max_uses)
        )

    def increment_usage(self):
        """Increment the usage count of this code"""
        self.times_used += 1
        if self.max_uses > 0 and self.times_used >= self.max_uses:
            self.is_active = False

class PopulationRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    population_count = db.Column(db.Integer)
    record_date = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.String(200))
    data_source = db.Column(db.String(100))  # e.g., 'survey', 'estimate', 'census'
    confidence_level = db.Column(db.Float)  # Statistical confidence in the count
    notes = db.Column(db.Text)

    # Relationship with Species
    species = db.relationship('Species', back_populates='population_records')

class HabitatData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    habitat_type = db.Column(db.String(100))  # e.g., 'forest', 'wetland', 'grassland'
    area_size = db.Column(db.Float)  # in square kilometers
    quality_score = db.Column(db.Integer)  # 1-10 rating of habitat quality
    threats = db.Column(db.Text)  # Documented threats to habitat
    record_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with Species
    species = db.relationship('Species', back_populates='habitats')

class MigrationPattern(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    start_location = db.Column(db.String(200), nullable=False)
    end_location = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    distance = db.Column(db.Float)  # in kilometers
    route_data = db.Column(db.Text)  # JSON string of route coordinates
    pattern_type = db.Column(db.String(50))  # e.g., 'seasonal', 'permanent', 'temporary'
    triggers = db.Column(db.String(200))  # What triggered the migration

    # Relationship with Species
    species = db.relationship('Species', back_populates='migrations')