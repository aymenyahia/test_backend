from flask import request, jsonify, session
from werkzeug.security import generate_password_hash
from database import db, User
from auth import ROLE_ADMIN, ROLE_MANAGER, ROLE_USER
from . import api_bp

@api_bp.route('/users', methods=['GET', 'POST'])
def api_users():
    current_role = session.get('user_role')
    
    if request.method == 'GET':
        if current_role == ROLE_USER:
            users = User.query.all()
            return jsonify([{
                "matricule": u.matricule, "name": u.name,
                "family_name": u.family_name, "user_name": u.user_name,
                "profil_pic_url": u.profil_pic_url
            } for u in users])
        
        users = User.query.all()
        return jsonify([{
            "matricule": u.matricule, "name": u.name, "family_name": u.family_name,
            "category": u.category, "grade": u.grade, "user_name": u.user_name,
            "profil_pic_url": u.profil_pic_url, "user_role": u.user_role,
            "role": u.role_rel.role if u.role_rel else None
        } for u in users])
    
    # POST requires admin
    if current_role != ROLE_ADMIN:
        return jsonify({"error": "Admin required"}), 403
    
    data = request.get_json()
    user = User(
        matricule=data['matricule'], name=data['name'],
        family_name=data['family_name'], category=data['category'],
        grade=data['grade'], user_name=data['user_name'],
        password=generate_password_hash(data['password']), profil_pic_url=data.get('profil_pic_url', ''),
        user_role=data.get('user_role', ROLE_USER)
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"matricule": user.matricule}), 201

@api_bp.route('/users/<matricule>', methods=['GET', 'PUT', 'DELETE'])
def api_user(matricule):
    user = User.query.get_or_404(matricule)
    current_role = session.get('user_role')
    
    if request.method == 'GET':
        return jsonify({
            "matricule": user.matricule, "name": user.name,
            "family_name": user.family_name, "category": user.category,
            "grade": user.grade, "user_name": user.user_name,
            "profil_pic_url": user.profil_pic_url,
            "user_role": user.user_role,
            "role": user.role_rel.role if user.role_rel else None
        })
    
    # PUT/DELETE requires admin
    if current_role != ROLE_ADMIN:
        return jsonify({"error": "Admin required"}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        user.name = data.get('name', user.name)
        user.family_name = data.get('family_name', user.family_name)
        user.category = data.get('category', user.category)
        user.grade = data.get('grade', user.grade)
        user.user_name = data.get('user_name', user.user_name)
        if 'password' in data: user.password = generate_password_hash(data['password'])
        user.profil_pic_url = data.get('profil_pic_url', user.profil_pic_url)
        user.user_role = data.get('user_role', user.user_role)
        db.session.commit()
        return jsonify({"matricule": user.matricule})
    
    elif request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Deleted"})