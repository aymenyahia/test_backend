from flask import request, jsonify
from database import db, P2PChat, GroupChat, GroupChatMembership
from . import api_bp

# --- P2P CHATS ---
@api_bp.route('/p2p-chats', methods=['GET', 'POST'])
def api_p2p_chats():
    if request.method == 'GET':
        chats = P2PChat.query.all()
        return jsonify([{
            "p2p_id": c.p2p_id,
            "first_user": c.first_user,
            "second_user": c.second_user,
            "created_at": c.created_at.isoformat() if c.created_at else None
        } for c in chats])
    
    data = request.get_json()
    chat = P2PChat(first_user=data['first_user'], second_user=data['second_user'])
    db.session.add(chat)
    db.session.commit()
    return jsonify({"p2p_id": chat.p2p_id}), 201

# --- GROUP CHATS ---
@api_bp.route('/group-chats', methods=['GET', 'POST'])
def api_group_chats():
    if request.method == 'GET':
        chats = GroupChat.query.all()
        return jsonify([{
            "group_chat_id": c.group_chat_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "task_id": c.task_id,
            "profil_pic_url": c.profil_pic_url
        } for c in chats])
    
    data = request.get_json()
    chat = GroupChat(
        task_id=data.get('task_id'),
        profil_pic_url=data.get('profil_pic_url', '')
    )
    db.session.add(chat)
    db.session.commit()
    return jsonify({"group_chat_id": chat.group_chat_id}), 201

@api_bp.route('/group-chats/<int:id>/members', methods=['GET', 'POST'])
def api_group_members(id):
    chat = GroupChat.query.get_or_404(id)
    if request.method == 'GET':
        members = GroupChatMembership.query.filter_by(group_id=id).all()
        return jsonify([{
            "group_chat_membership_id": m.group_chat_membership_id,
            "user_id": m.user_id,
            "is_creater": m.is_creater
        } for m in members])
    
    data = request.get_json()
    member = GroupChatMembership(
        user_id=data['user_id'],
        group_id=id,
        is_creater=data.get('is_creater', 0)
    )
    db.session.add(member)
    db.session.commit()
    return jsonify({"group_chat_membership_id": member.group_chat_membership_id}), 201