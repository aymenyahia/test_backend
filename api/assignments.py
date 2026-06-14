from flask import request, jsonify
from database import db, Assignment
from . import api_bp

@api_bp.route('/assignments', methods=['GET', 'POST'])
def api_assignments():
    if request.method == 'GET':
        assignments = Assignment.query.all()
        return jsonify([{
            "assignement_id": a.assignement_id,
            "user_id": a.user_id,
            "task_id": a.task_id
        } for a in assignments])
    
    data = request.get_json()
    assignment = Assignment(user_id=data['user_id'], task_id=data['task_id'])
    db.session.add(assignment)
    db.session.commit()
    return jsonify({"assignement_id": assignment.assignement_id}), 201

@api_bp.route('/assignments/<int:id>', methods=['GET', 'DELETE'])
def api_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            "assignement_id": assignment.assignement_id,
            "user_id": assignment.user_id,
            "task_id": assignment.task_id
        })
    elif request.method == 'DELETE':
        db.session.delete(assignment)
        db.session.commit()
        return jsonify({"message": "Deleted"})