from flask import request, jsonify, session
from sqlalchemy import text
from database import db
from auth import ROLE_ADMIN
from . import api_bp

@api_bp.route('/sql', methods=['POST'])
def api_sql():
    # Only admin can execute SQL
    if session.get('user_role') != ROLE_ADMIN:
        return jsonify({"error": "Admin access required"}), 403
    
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    query_upper = query.upper()
    allowed = any(query_upper.startswith(p) for p in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'PRAGMA'])
    if not allowed:
        return jsonify({"error": "Only SELECT, INSERT, UPDATE, DELETE, PRAGMA allowed"}), 403
    
    try:
        result = db.session.execute(text(query))
        db.session.commit()
        
        if query_upper.startswith('SELECT') or query_upper.startswith('PRAGMA'):
            rows = result.fetchall()
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in rows]
            return jsonify({"columns": list(columns), "rows": data, "count": len(data)})
        return jsonify({"message": "Query executed", "rowcount": result.rowcount})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@api_bp.route('/search/<table>', methods=['GET'])
def api_search(table):
    search_term = request.args.get('q', '')
    if not search_term:
        return jsonify({"error": "No search term"}), 400
    
    from database import User, Grade, Category, ToDoTask
    
    models = {'users': User, 'grades': Grade, 'categories': Category, 'tasks': ToDoTask}
    model = models.get(table)
    if not model:
        return jsonify({"error": "Unknown table"}), 400
    
    if table == 'users':
        results = model.query.filter(db.or_(
            model.name.contains(search_term), model.family_name.contains(search_term),
            model.matricule.contains(search_term), model.user_name.contains(search_term)
        )).all()
    elif table == 'grades':
        results = model.query.filter(model.grade_name.contains(search_term)).all()
    elif table == 'categories':
        results = model.query.filter(model.category_name.contains(search_term)).all()
    elif table == 'tasks':
        results = model.query.filter(db.or_(model.title.contains(search_term), model.description.contains(search_term))).all()
    else:
        results = []
    
    data = []
    for item in results:
        row = {}
        for col in model.__table__.columns:
            val = getattr(item, col.name)
            row[col.name] = val.isoformat() if hasattr(val, 'isoformat') else val
        data.append(row)
    return jsonify({"count": len(data), "results": data})