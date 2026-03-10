from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message='Введите email'), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(message='Введите пароль')])
    remember = BooleanField('Запомнить меня', default=False)


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message='Введите email'), Email()])
    password = PasswordField('Пароль', validators=[
        DataRequired(),
        Length(min=6, message='Пароль должен быть не менее 6 символов')
    ])
    password_confirm = PasswordField('Подтвердите пароль', validators=[
        DataRequired(),
        EqualTo('password', message='Пароли не совпадают')
    ])
    role = SelectField('Роль', choices=[
        ('student', 'Ученик'),
        ('tutor', 'Репетитор')
    ], validators=[DataRequired()])
