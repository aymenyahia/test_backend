from flask import request, jsonify
from database import db, Category
from . import api_bp

@api_bp.route('/categories', methods=['GET', 'POST'])
def api_categories():
    if request.method == 'GET':
        cats = Category.query.all()
        return jsonify([{"category_id": c.category_id, "category_name": c.category_name} for c in cats])
    
    data = request.get_json()
    cat = Category(category_name=data['category_name'])
    db.session.add(cat)
    db.session.commit()
    return jsonify({"category_id": cat.category_id, "category_name": cat.category_name}), 201

@api_bp.route('/categories/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_category(id):
    cat = Category.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({"category_id": cat.category_id, "category_name": cat.category_name})
    elif request.method == 'PUT':
        data = request.get_json()
        cat.category_name = data.get('category_name', cat.category_name)
        db.session.commit()
        return jsonify({"category_id": cat.category_id, "category_name": cat.category_name})
    elif request.method == 'DELETE':
        db.session.delete(cat)
        db.session.commit()
        return jsonify({"message": "Deleted"})