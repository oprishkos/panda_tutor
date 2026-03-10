from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.models import User, TutorProfile, StudentProfile, Booking, Payment
from app import db
from sqlalchemy import func


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Доступ только для администраторов.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@login_required
@admin_required
def index():
    total_users = User.query.count()
    total_tutors = TutorProfile.query.count()
    total_bookings = Booking.query.count()
    completed_bookings = Booking.query.filter_by(status='completed').count()
    revenue_result = db.session.query(func.sum(Payment.amount)).filter(Payment.status == 'completed').scalar()
    total_revenue = float(revenue_result or 0)
    commission_result = db.session.query(func.sum(Payment.commission)).filter(Payment.status == 'completed').scalar()
    total_commission = float(commission_result or 0)
    return render_template('admin/index.html',
                           total_users=total_users,
                           total_tutors=total_tutors,
                           total_bookings=total_bookings,
                           total_lessons=completed_bookings,
                           total_revenue=total_revenue,
                           total_commission=total_commission)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    q = request.args.get('q', '').strip()
    query = User.query
    if q:
        query = query.filter(User.email.ilike(f'%{q}%'))
    users_list = query.order_by(User.created_at.desc()).limit(100).all()
    return render_template('admin/users.html', users=users_list, search_query=q)


@admin_bp.route('/bookings')
@login_required
@admin_required
def bookings():
    bookings_list = Booking.query.order_by(Booking.created_at.desc()).limit(200).all()
    return render_template('admin/bookings.html', bookings=bookings_list)


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Нельзя деактивировать себя.', 'error')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'Пользователь {"активирован" if user.is_active else "деактивирован"}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/tutors/<int:tutor_id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_tutor(tutor_id):
    tutor = TutorProfile.query.get_or_404(tutor_id)
    tutor.is_verified = not tutor.is_verified
    db.session.commit()
    flash(f'Репетитор {"верифицирован" if tutor.is_verified else "снят с верификации"}.', 'success')
    return redirect(request.referrer or url_for('admin.index'))
