from flask import current_app
from flask_mail import Message


def send_booking_notification(booking, event_type):
    """Send email on booking status change. event_type: new_booking, confirmed, declined, cancelled."""
    if not current_app.config.get('MAIL_USERNAME'):
        return
    from app.models import TutorProfile, StudentProfile
    tutor = TutorProfile.query.get(booking.tutor_id)
    student = StudentProfile.query.get(booking.student_id)
    if not tutor or not student:
        return
    tutor_email = tutor.user.email
    student_email = student.user.email
    subject_map = {
        'new_booking': 'Новая заявка на урок',
        'confirmed': 'Бронирование подтверждено',
        'declined': 'Репетитор отклонил заявку',
        'cancelled': 'Бронирование отменено',
    }
    subject = subject_map.get(event_type, 'Уведомление о бронировании')
    body = f'Здравствуйте.\n\nБронирование #{booking.id}: {event_type}.\nРепетитор: {tutor.full_name}\nУченик: {student.full_name}\n\nС уважением,\nПлатформа репетиторов.'
    msg = Message(subject=subject, body=body, recipients=[])
    if event_type == 'new_booking':
        msg.recipients = [tutor_email]
    else:
        msg.recipients = [student_email]
    try:
        from flask_mail import Mail
        mail = current_app.extensions.get('mail')
        if mail:
            mail.send(msg)
    except Exception:
        pass
