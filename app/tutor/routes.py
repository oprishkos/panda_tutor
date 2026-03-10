from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.tutor import tutor_bp
from app.models import TutorProfile, Booking, TimeSlot, Lesson
from app import db
from app.tutor.forms import TutorProfileForm, TimeSlotForm
from datetime import datetime, date, time


def get_tutor_profile():
    return TutorProfile.query.filter_by(user_id=current_user.id).first()


def tutor_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_tutor:
            flash('Доступ только для репетиторов.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


@tutor_bp.route('/dashboard')
@login_required
@tutor_required
def dashboard():
    profile = get_tutor_profile()
    upcoming = Booking.query.filter_by(tutor_id=profile.id).filter(
        Booking.status.in_(['pending', 'confirmed'])
    ).order_by(Booking.created_at.desc()).limit(20).all()
    for b in upcoming:
        b.slot = TimeSlot.query.get(b.slot_id)
    completed_bookings = Booking.query.filter_by(tutor_id=profile.id, status='completed').all()
    total_earnings = 0
    for b in completed_bookings:
        if b.payment and b.payment.status == 'completed':
            total_earnings += float(b.payment.amount or 0) - float(b.payment.commission or 0)
    reviews = Lesson.query.join(Booking).filter(Booking.tutor_id == profile.id, Lesson.review_text.isnot(None)).order_by(
        Lesson.created_at.desc()
    ).limit(10).all()
    return render_template('tutor/dashboard.html', profile=profile, upcoming=upcoming,
                           total_earnings=total_earnings, reviews=reviews)


@tutor_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@tutor_required
def profile():
    profile = get_tutor_profile()
    form = TutorProfileForm(obj=profile)
    if form.validate_on_submit():
        form.populate_obj(profile)
        profile.subjects = form.subjects.data or ''
        db.session.commit()
        flash('Профиль обновлён.', 'success')
        return redirect(url_for('tutor.dashboard'))
    return render_template('tutor/profile.html', form=form, profile=profile)


@tutor_bp.route('/slots', methods=['GET', 'POST'])
@login_required
@tutor_required
def slots():
    profile = get_tutor_profile()
    form = TimeSlotForm()
    if form.validate_on_submit():
        slot = TimeSlot(
            tutor_id=profile.id,
            date=form.date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            is_booked=False
        )
        db.session.add(slot)
        db.session.commit()
        flash('Слот добавлен.', 'success')
        return redirect(url_for('tutor.slots'))
    slots_list = TimeSlot.query.filter_by(tutor_id=profile.id).order_by(TimeSlot.date, TimeSlot.start_time).all()
    return render_template('tutor/slots.html', form=form, slots=slots_list)


@tutor_bp.route('/slots/<int:slot_id>/delete', methods=['POST'])
@login_required
@tutor_required
def delete_slot(slot_id):
    profile = get_tutor_profile()
    slot = TimeSlot.query.get_or_404(slot_id)
    if slot.tutor_id != profile.id:
        flash('Нет доступа.', 'error')
        return redirect(url_for('tutor.slots'))
    if slot.is_booked:
        flash('Нельзя удалить занятый слот.', 'error')
        return redirect(url_for('tutor.slots'))
    db.session.delete(slot)
    db.session.commit()
    flash('Слот удалён.', 'success')
    return redirect(url_for('tutor.slots'))


@tutor_bp.route('/booking/<int:booking_id>/confirm', methods=['POST'])
@login_required
@tutor_required
def confirm_booking(booking_id):
    profile = get_tutor_profile()
    booking = Booking.query.get_or_404(booking_id)
    if booking.tutor_id != profile.id or booking.status != 'pending':
        flash('Невозможно подтвердить.', 'error')
        return redirect(url_for('tutor.dashboard'))
    booking.status = 'confirmed'
    db.session.commit()
    from app.utils.email import send_booking_notification
    send_booking_notification(booking, 'confirmed')
    flash('Бронирование подтверждено. Ученик может оплатить урок.', 'success')
    return redirect(url_for('tutor.dashboard'))


@tutor_bp.route('/booking/<int:booking_id>/decline', methods=['POST'])
@login_required
@tutor_required
def decline_booking(booking_id):
    profile = get_tutor_profile()
    booking = Booking.query.get_or_404(booking_id)
    if booking.tutor_id != profile.id or booking.status != 'pending':
        flash('Невозможно отклонить.', 'error')
        return redirect(url_for('tutor.dashboard'))
    slot = TimeSlot.query.get(booking.slot_id)
    if slot:
        slot.is_booked = False
    booking.status = 'cancelled'
    db.session.commit()
    from app.utils.email import send_booking_notification
    send_booking_notification(booking, 'declined')
    flash('Бронирование отклонено.', 'success')
    return redirect(url_for('tutor.dashboard'))


@tutor_bp.route('/booking/<int:booking_id>/complete', methods=['POST'])
@login_required
@tutor_required
def complete_booking(booking_id):
    profile = get_tutor_profile()
    booking = Booking.query.get_or_404(booking_id)
    if booking.tutor_id != profile.id or booking.status != 'confirmed':
        flash('Невозможно завершить.', 'error')
        return redirect(url_for('tutor.dashboard'))
    booking.status = 'completed'
    if not Lesson.query.filter_by(booking_id=booking.id).first():
        lesson = Lesson(booking_id=booking.id)
        db.session.add(lesson)
    db.session.commit()
    flash('Урок отмечен как проведённый. Ученик может оставить отзыв.', 'success')
    return redirect(url_for('tutor.dashboard'))
