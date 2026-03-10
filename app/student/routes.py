from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.student import student_bp
from app.models import StudentProfile, Booking, TutorProfile, FavoriteTutor, TimeSlot, Lesson
from app import db
from app.student.forms import StudentProfileForm, ReviewForm
from datetime import datetime, date, time


def get_student_profile():
    return StudentProfile.query.filter_by(user_id=current_user.id).first()


def student_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_student:
            flash('Доступ только для учеников.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    profile = get_student_profile()
    upcoming = Booking.query.filter_by(student_id=profile.id).filter(
        Booking.status.in_(['pending', 'confirmed'])
    ).order_by(Booking.created_at.desc()).limit(20).all()
    for b in upcoming:
        b.slot = TimeSlot.query.get(b.slot_id)
        b.tutor = TutorProfile.query.get(b.tutor_id)
    history = Booking.query.filter_by(student_id=profile.id).filter(
        Booking.status.in_(['completed', 'cancelled'])
    ).order_by(Booking.created_at.desc()).limit(20).all()
    for b in history:
        b.slot = TimeSlot.query.get(b.slot_id)
        b.tutor = TutorProfile.query.get(b.tutor_id)
    favorites = FavoriteTutor.query.filter_by(student_id=profile.id).all()
    fav_tutors = [TutorProfile.query.get(f.tutor_id) for f in favorites]
    for t in fav_tutors:
        if t:
            t._rating = t.average_rating()
    unread = sum(1 for _ in range(1))  # placeholder, will use Message model in chat
    return render_template('student/dashboard.html', profile=profile, upcoming=upcoming,
                           history=history, favorites=fav_tutors)


@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
def profile():
    profile = get_student_profile()
    form = StudentProfileForm(obj=profile)
    if form.validate_on_submit():
        form.populate_obj(profile)
        profile.subjects_of_interest = form.subjects_of_interest.data or ''
        db.session.commit()
        flash('Профиль обновлён.', 'success')
        return redirect(url_for('student.dashboard'))
    return render_template('student/profile.html', form=form, profile=profile)


@student_bp.route('/book/<int:tutor_id>/<int:slot_id>', methods=['POST'])
@login_required
@student_required
def book_lesson(tutor_id, slot_id):
    profile = get_student_profile()
    slot = TimeSlot.query.get_or_404(slot_id)
    if slot.tutor_id != tutor_id or slot.is_booked:
        flash('Слот недоступен.', 'error')
        return redirect(url_for('main.tutor_profile', tutor_id=tutor_id))
    booking = Booking(student_id=profile.id, tutor_id=tutor_id, slot_id=slot_id, status='pending')
    db.session.add(booking)
    slot.is_booked = True
    db.session.commit()
    from app.utils.email import send_booking_notification
    send_booking_notification(booking, 'new_booking')
    flash('Заявка на урок отправлена. Ожидайте подтверждения репетитора.', 'success')
    return redirect(url_for('student.dashboard'))


@student_bp.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
@student_required
def cancel_booking(booking_id):
    profile = get_student_profile()
    booking = Booking.query.get_or_404(booking_id)
    if booking.student_id != profile.id:
        flash('Нет доступа.', 'error')
        return redirect(url_for('student.dashboard'))
    if booking.status not in ('pending', 'confirmed'):
        flash('Невозможно отменить.', 'error')
        return redirect(url_for('student.dashboard'))
    slot = TimeSlot.query.get(booking.slot_id)
    if slot:
        slot.is_booked = False
    booking.status = 'cancelled'
    db.session.commit()
    from app.utils.email import send_booking_notification
    send_booking_notification(booking, 'cancelled')
    flash('Бронирование отменено.', 'success')
    return redirect(url_for('student.dashboard'))


@student_bp.route('/favorite/<int:tutor_id>', methods=['POST'])
@login_required
@student_required
def add_favorite(tutor_id):
    profile = get_student_profile()
    if FavoriteTutor.query.filter_by(student_id=profile.id, tutor_id=tutor_id).first():
        flash('Репетитор уже в избранном.', 'info')
    else:
        fav = FavoriteTutor(student_id=profile.id, tutor_id=tutor_id)
        db.session.add(fav)
        db.session.commit()
        flash('Репетитор добавлен в избранное.', 'success')
    return redirect(request.referrer or url_for('main.tutors'))


@student_bp.route('/favorite/<int:tutor_id>/remove', methods=['POST'])
@login_required
@student_required
def remove_favorite(tutor_id):
    profile = get_student_profile()
    fav = FavoriteTutor.query.filter_by(student_id=profile.id, tutor_id=tutor_id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
        flash('Репетитор удалён из избранного.', 'success')
    return redirect(request.referrer or url_for('student.dashboard'))


@student_bp.route('/booking/<int:booking_id>/review', methods=['GET', 'POST'])
@login_required
@student_required
def leave_review(booking_id):
    profile = get_student_profile()
    booking = Booking.query.get_or_404(booking_id)
    if booking.student_id != profile.id or booking.status != 'completed':
        flash('Невозможно оставить отзыв.', 'error')
        return redirect(url_for('student.dashboard'))
    lesson = Lesson.query.filter_by(booking_id=booking.id).first()
    if not lesson:
        lesson = Lesson(booking_id=booking.id)
        db.session.add(lesson)
        db.session.commit()
    if lesson.rating and lesson.review_text:
        flash('Вы уже оставили отзыв.', 'info')
        return redirect(url_for('student.dashboard'))
    form = ReviewForm()
    if form.validate_on_submit():
        lesson.subject = form.subject.data
        lesson.notes = form.notes.data
        lesson.rating = form.rating.data
        lesson.review_text = form.review_text.data
        db.session.commit()
        flash('Спасибо за отзыв!', 'success')
        return redirect(url_for('student.dashboard'))
    return render_template('student/review.html', form=form, booking=booking)
