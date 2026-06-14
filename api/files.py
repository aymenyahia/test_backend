from flask import request, jsonify
from database import db, P2PFile, GroupFile
from . import api_bp

@api_bp.route('/p2p-chats/<int:id>/files', methods=['GET', 'POST'])
def api_p2p_files(id):
    from database import P2PChat
    chat = P2PChat.query.get_or_404(id)
    if request.method == 'GET':
        files = P2PFile.query.filter_by(chat_id=id).all()
        return jsonify([{
            "p2p_file_id": f.p2p_file_id,
            "creater": f.creater,
            "url": f.url,
            "date": f.date.isoformat() if f.date else None
        } for f in files])
    
    data = request.get_json()
    file = P2PFile(creater=data['creater'], url=data['url'], chat_id=id)
    db.session.add(file)
    db.session.commit()
    return jsonify({"p2p_file_id": file.p2p_file_id}), 201

@api_bp.route('/group-chats/<int:id>/files', methods=['GET', 'POST'])
def api_group_files(id):
    from database import GroupChat
    chat = GroupChat.query.get_or_404(id)
    if request.method == 'GET':
        files = GroupFile.query.filter_by(chat_id=id).all()
        return jsonify([{
            "group_file_id": f.group_file_id,
            "creater": f.creater,
            "url": f.url,
            "date": f.date.isoformat() if f.date else None
        } for f in files])
    
    data = request.get_json()
    file = GroupFile(creater=data['creater'], url=data['url'], chat_id=id)
    db.session.add(file)
    db.session.commit()
    return jsonify({"group_file_id": file.group_file_id}), 201