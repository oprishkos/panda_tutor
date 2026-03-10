from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.auth import auth_bp
from app.auth.forms import LoginForm, RegisterForm
from app.models import User, TutorProfile, StudentProfile
from app import db


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash('Пользователь с таким email уже зарегистрирован.', 'error')
            return render_template('auth/register.html', form=form)
        user = User(email=form.email.data.lower(), role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        if user.role == 'tutor':
            profile = TutorProfile(user_id=user.id, full_name='', bio='', subjects='', hourly_rate=0)
            db.session.add(profile)
        else:
            profile = StudentProfile(user_id=user.id, full_name='', subjects_of_interest='')
            db.session.add(profile)
        db.session.commit()
        login_user(user)
        flash('Регистрация успешна! Заполните профиль.', 'success')
        if user.role == 'tutor':
            return redirect(url_for('tutor.dashboard'))
        return redirect(url_for('student.dashboard'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверный email или пароль.', 'error')
            return render_template('auth/login.html', form=form)
        if not user.is_active:
            flash('Аккаунт деактивирован.', 'error')
            return render_template('auth/login.html', form=form)
        login_user(user, remember=form.remember.data)
        next_page = request.args.get('next') or url_for('main.index')
        flash('Вы вошли в систему.', 'success')
        return redirect(next_page)
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('main.index'))
