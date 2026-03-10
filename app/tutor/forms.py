from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, BooleanField, DateField, TimeField
from wtforms.validators import DataRequired, Optional, NumberRange


class TutorProfileForm(FlaskForm):
    full_name = StringField('Имя', validators=[DataRequired(message='Введите имя')])
    bio = TextAreaField('О себе', validators=[Optional()])
    subjects = StringField('Предметы (через запятую)', validators=[DataRequired(message='Укажите предметы')])
    experience = StringField('Опыт (например: 5 лет)', validators=[Optional()])
    hourly_rate = DecimalField('Ставка за час (₽)', places=2, validators=[DataRequired(), NumberRange(0)])
    photo_url = StringField('URL фото', validators=[Optional()])


class TimeSlotForm(FlaskForm):
    date = DateField('Дата', validators=[DataRequired()])
    start_time = TimeField('Начало', validators=[DataRequired()])
    end_time = TimeField('Конец', validators=[DataRequired()])
