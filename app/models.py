from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student, tutor, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    tutor_profile = db.relationship('TutorProfile', backref='user', uselist=False, lazy='joined')
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, lazy='joined')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_tutor(self):
        return self.role == 'tutor'

    @property
    def is_student(self):
        return self.role == 'student'

    def __repr__(self):
        return f'<User {self.email}>'


class TutorProfile(db.Model):
    __tablename__ = 'tutor_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    subjects = db.Column(db.String(500), nullable=False)  # comma-separated
    experience = db.Column(db.String(200))  # e.g. "5 years"
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=False)
    photo_url = db.Column(db.String(500))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    time_slots = db.relationship('TimeSlot', backref='tutor', lazy='dynamic', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', foreign_keys='Booking.tutor_id', backref='tutor', lazy='dynamic')
    favorites = db.relationship('FavoriteTutor', backref='tutor', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def subjects_list(self):
        return [s.strip() for s in self.subjects.split(',')] if self.subjects else []

    def average_rating(self):
        from sqlalchemy import func
        result = db.session.query(func.avg(Lesson.rating)).join(Booking).filter(
            Booking.tutor_id == self.id,
            Lesson.rating.isnot(None)
        ).scalar()
        return round(float(result or 0), 1)

    def reviews_count(self):
        return Lesson.query.join(Booking).filter(Booking.tutor_id == self.id, Lesson.review_text.isnot(None)).count()

    def __repr__(self):
        return f'<TutorProfile {self.full_name}>'


class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    subjects_of_interest = db.Column(db.String(500))  # comma-separated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bookings = db.relationship('Booking', backref='student', lazy='dynamic')
    favorites = db.relationship('FavoriteTutor', backref='student', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def subjects_list(self):
        return [s.strip() for s in (self.subjects_of_interest or '').split(',')] if self.subjects_of_interest else []

    def __repr__(self):
        return f'<StudentProfile {self.full_name}>'


class FavoriteTutor(db.Model):
    __tablename__ = 'favorite_tutors'
    __table_args__ = (db.UniqueConstraint('student_id', 'tutor_id', name='uq_favorite_student_tutor'),)
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TimeSlot(db.Model):
    __tablename__ = 'time_slots'
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    booking = db.relationship('Booking', backref='slot', uselist=False, lazy='joined')

    def __repr__(self):
        return f'<TimeSlot {self.date} {self.start_time}-{self.end_time}>'


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('time_slots.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lesson = db.relationship('Lesson', backref='booking', uselist=False, lazy='joined')
    payment = db.relationship('Payment', backref='booking', uselist=False, lazy='joined')

    def __repr__(self):
        return f'<Booking {self.id} {self.status}>'


class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, unique=True)
    subject = db.Column(db.String(100))
    notes = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1-5
    review_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Lesson {self.id}>'


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

    def __repr__(self):
        return f'<Message {self.id}>'


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    commission = db.Column(db.Numeric(10, 2), default=0)
    stripe_payment_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')  # pending, completed, refunded, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.id} {self.status}>'
