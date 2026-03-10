from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app import socketio
from app.models import Message
from app import db


@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')
        emit('status', {'msg': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        leave_room(f'user_{current_user.id}')


@socketio.on('send_message')
def handle_message(data):
    if not current_user.is_authenticated:
        return
    receiver_id = data.get('receiver_id', type=int)
    text = (data.get('text') or '').strip()
    if not receiver_id or not text:
        return
    msg = Message(sender_id=current_user.id, receiver_id=receiver_id, text=text)
    db.session.add(msg)
    db.session.commit()
    room = f'user_{receiver_id}'
    emit('new_message', {
        'id': msg.id,
        'sender_id': current_user.id,
        'receiver_id': receiver_id,
        'text': text,
        'timestamp': msg.timestamp.isoformat(),
    }, room=room)
    emit('new_message', {
        'id': msg.id,
        'sender_id': current_user.id,
        'receiver_id': receiver_id,
        'text': text,
        'timestamp': msg.timestamp.isoformat(),
    }, room=f'user_{current_user.id}')


@socketio.on('join_conversation')
def handle_join_conversation(data):
    if current_user.is_authenticated:
        other_id = data.get('user_id', type=int)
        if other_id:
            room = f'conv_{min(current_user.id, other_id)}_{max(current_user.id, other_id)}'
            join_room(room)
