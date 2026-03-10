from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Optional, NumberRange


class StudentProfileForm(FlaskForm):
    full_name = StringField('Имя', validators=[DataRequired(message='Введите имя')])
    age = IntegerField('Возраст', validators=[Optional(), NumberRange(5, 120)])
    subjects_of_interest = StringField('Интересующие предметы (через запятую)', validators=[Optional()])


class ReviewForm(FlaskForm):
    subject = StringField('Предмет', validators=[Optional()])
    notes = TextAreaField('Заметки', validators=[Optional()])
    rating = SelectField('Оценка', choices=[(i, str(i)) for i in range(1, 6)], coerce=int, validators=[DataRequired()])
    review_text = TextAreaField('Отзыв', validators=[DataRequired(message='Напишите отзыв')])
