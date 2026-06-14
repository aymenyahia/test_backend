from flask import request, jsonify
from database import db, P2PMessage, GroupMessage
from . import api_bp

# --- P2P MESSAGES ---
@api_bp.route('/p2p-chats/<int:id>/messages', methods=['GET', 'POST'])
def api_p2p_messages(id):
    from database import P2PChat
    chat = P2PChat.query.get_or_404(id)
    if request.method == 'GET':
        messages = P2PMessage.query.filter_by(chat_id=id).all()
        return jsonify([{
            "p2p_message_id": m.p2p_message_id,
            "user_id": m.user_id,
            "content": m.content,
            "date": m.date.isoformat() if m.date else None
        } for m in messages])
    
    data = request.get_json()
    msg = P2PMessage(user_id=data['user_id'], chat_id=id, content=data['content'])
    db.session.add(msg)
    db.session.commit()
    return jsonify({"p2p_message_id": msg.p2p_message_id}), 201

# --- GROUP MESSAGES ---
@api_bp.route('/group-chats/<int:id>/messages', methods=['GET', 'POST'])
def api_group_messages(id):
    from database import GroupChat
    chat = GroupChat.query.get_or_404(id)
    if request.method == 'GET':
        messages = GroupMessage.query.filter_by(chat_id=id).all()
        return jsonify([{
            "group_message_id": m.group_message_id,
            "user_id": m.user_id,
            "content": m.content,
            "date": m.date.isoformat() if m.date else None
        } for m in messages])
    
    data = request.get_json()
    msg = GroupMessage(user_id=data['user_id'], chat_id=id, content=data['content'])
    db.session.add(msg)
    db.session.commit()
    return jsonify({"group_message_id": msg.group_message_id}), 201