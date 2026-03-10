from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import csrf
from app.payments import payments_bp
from app.models import Booking, Payment, TutorProfile, StudentProfile
from app import db
import stripe


def get_stripe():
    key = current_app.config.get('STRIPE_SECRET_KEY')
    if key:
        stripe.api_key = key
    return stripe


@payments_bp.route('/checkout/<int:booking_id>')
@login_required
def checkout(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.status != 'confirmed':
        flash('Бронирование не подтверждено или уже оплачено.', 'error')
        return redirect(url_for('student.dashboard'))
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile or booking.student_id != profile.id:
        flash('Нет доступа.', 'error')
        return redirect(url_for('main.index'))
    tutor = TutorProfile.query.get(booking.tutor_id)
    amount_cents = int(float(tutor.hourly_rate) * 100)
    if amount_cents < 50:
        amount_cents = 50
    existing = Payment.query.filter_by(booking_id=booking_id).first()
    if existing and existing.status == 'completed':
        flash('Оплата уже произведена.', 'info')
        return redirect(url_for('student.dashboard'))
    if not existing:
        commission_rub = float(tutor.hourly_rate) * (current_app.config.get('PLATFORM_COMMISSION_PERCENT', 15) / 100)
        payment = Payment(booking_id=booking_id, amount=float(tutor.hourly_rate), commission=commission_rub, status='pending')
        db.session.add(payment)
        db.session.commit()
    else:
        payment = existing
    stripe_key = current_app.config.get('STRIPE_SECRET_KEY')
    if not stripe_key:
        payment.status = 'completed'
        db.session.commit()
        flash('Оплата в демо-режиме засчитана. Stripe не настроен.', 'success')
        return redirect(url_for('student.dashboard'))
    try:
        get_stripe()
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'rub',
                    'product_data': {'name': f'Урок с {tutor.full_name}', 'description': 'Онлайн-урок'},
                    'unit_amount': amount_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.host_url.rstrip('/') + url_for('payments.success', booking_id=booking_id),
            cancel_url=request.host_url.rstrip('/') + url_for('student.dashboard'),
            metadata={'booking_id': str(booking_id), 'payment_id': str(payment.id)},
        )
        return redirect(session.url)
    except Exception as e:
        flash(f'Ошибка создания сессии оплаты: {e}', 'error')
        return redirect(url_for('student.dashboard'))


@payments_bp.route('/success/<int:booking_id>')
@login_required
def success(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    payment = Payment.query.filter_by(booking_id=booking_id).first()
    if payment:
        payment.status = 'completed'
        db.session.commit()
    flash('Оплата прошла успешно.', 'success')
    return redirect(url_for('student.dashboard'))


@payments_bp.route('/webhook', methods=['POST'])
@csrf.exempt
def webhook():
    payload = request.get_data()
    sig = request.headers.get('Stripe-Signature', '')
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
    if webhook_secret:
        try:
            get_stripe()
            event = stripe.Webhook.construct_event(payload, sig, webhook_secret)
        except Exception:
            return '', 400
    else:
        import json
        event = json.loads(payload) if payload else None
    if event and event.get('type') == 'checkout.session.completed':
        session = event.get('data', {}).get('object', {})
        mid = session.get('metadata', {}).get('payment_id')
        if mid:
            payment = Payment.query.get(mid)
            if payment:
                payment.status = 'completed'
                payment.stripe_payment_id = session.get('payment_intent') or session.get('id')
                db.session.commit()
    return '', 200


@payments_bp.route('/refund/<int:booking_id>', methods=['POST'])
@login_required
def refund(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    payment = Payment.query.filter_by(booking_id=booking_id).first()
    if not payment or payment.status != 'completed':
        flash('Невозможно вернуть оплату.', 'error')
        return redirect(url_for('student.dashboard'))
    if payment.stripe_payment_id and current_app.config.get('STRIPE_SECRET_KEY'):
        try:
            get_stripe()
            stripe.Refund.create(payment_intent=payment.stripe_payment_id)
        except Exception:
            pass
    payment.status = 'refunded'
    from app.models import TimeSlot
    slot = booking.slot
    if slot:
        slot.is_booked = False
    booking.status = 'cancelled'
    db.session.commit()
    flash('Возврат оформлен.', 'success')
    return redirect(url_for('student.dashboard'))
