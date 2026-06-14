from flask import request, jsonify
from database import db, Grade
from . import api_bp

@api_bp.route('/grades', methods=['GET', 'POST'])
def api_grades():
    if request.method == 'GET':
        grades = Grade.query.all()
        return jsonify([{"grade_id": g.grade_id, "grade_name": g.grade_name} for g in grades])
    
    data = request.get_json()
    grade = Grade(grade_name=data['grade_name'])
    db.session.add(grade)
    db.session.commit()
    return jsonify({"grade_id": grade.grade_id, "grade_name": grade.grade_name}), 201

@api_bp.route('/grades/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_grade(id):
    grade = Grade.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({"grade_id": grade.grade_id, "grade_name": grade.grade_name})
    elif request.method == 'PUT':
        data = request.get_json()
        grade.grade_name = data.get('grade_name', grade.grade_name)
        db.session.commit()
        return jsonify({"grade_id": grade.grade_id, "grade_name": grade.grade_name})
    elif request.method == 'DELETE':
        db.session.delete(grade)
        db.session.commit()
        return jsonify({"message": "Deleted"})