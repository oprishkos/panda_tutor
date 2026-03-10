from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app.chat import chat_bp
from app.models import User, Message
from sqlalchemy import or_


def get_conversation_partners():
    """Users with whom current_user has exchanged messages."""
    sub = Message.query.filter(
        or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
    ).with_entities(Message.sender_id, Message.receiver_id).distinct()
    partner_ids = set()
    for row in sub:
        other_id = row[1] if row[0] == current_user.id else row[0]
        partner_ids.add(other_id)
    return User.query.filter(User.id.in_(partner_ids)).all() if partner_ids else []


@chat_bp.route('/')
@login_required
def index():
    partners = get_conversation_partners()
    return render_template('chat/index.html', partners=partners)


@chat_bp.route('/with/<int:user_id>')
@login_required
def conversation(user_id):
    other = User.query.get_or_404(user_id)
    if other.id == current_user.id:
        return redirect(url_for('chat.index'))
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other.id)) |
        ((Message.sender_id == other.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()
    for m in messages:
        if m.receiver_id == current_user.id:
            m.is_read = True
    from app import db
    db.session.commit()
    return render_template('chat/conversation.html', other=other, messages=messages)
