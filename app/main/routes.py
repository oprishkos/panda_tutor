from flask import render_template, request
from app.main import main_bp
from app.models import TutorProfile, Booking, Lesson, TimeSlot


@main_bp.route('/')
def index():
    top_tutors = TutorProfile.query.filter_by(is_verified=True).limit(6).all()
    for t in top_tutors:
        t._rating = t.average_rating()
    return render_template('index.html', top_tutors=top_tutors)


@main_bp.route('/tutors')
def tutors():
    q = request.args.get('q', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    min_rating = request.args.get('min_rating', type=float)
    query = TutorProfile.query
    if q:
        query = query.filter(TutorProfile.subjects.ilike(f'%{q}%') | TutorProfile.full_name.ilike(f'%{q}%'))
    if min_price is not None:
        query = query.filter(TutorProfile.hourly_rate >= min_price)
    if max_price is not None:
        query = query.filter(TutorProfile.hourly_rate <= max_price)
    tutors_list = query.all()
    if min_rating is not None:
        tutors_list = [t for t in tutors_list if t.average_rating() >= min_rating]
    for t in tutors_list:
        t._rating = t.average_rating()
    return render_template('main/tutors.html', tutors=tutors_list, search_query=q,
                           min_price=min_price, max_price=max_price, min_rating=min_rating)


@main_bp.route('/tutors/<int:tutor_id>')
def tutor_profile(tutor_id):
    tutor = TutorProfile.query.get_or_404(tutor_id)
    tutor._rating = tutor.average_rating()
    available_slots = TimeSlot.query.filter_by(tutor_id=tutor_id, is_booked=False).order_by(
        TimeSlot.date, TimeSlot.start_time
    ).limit(50).all()
    reviews = Lesson.query.join(Booking).filter(Booking.tutor_id == tutor_id, Lesson.review_text.isnot(None)).order_by(
        Lesson.created_at.desc()
    ).limit(10).all()
    return render_template('main/tutor_profile.html', tutor=tutor, available_slots=available_slots, reviews=reviews)
