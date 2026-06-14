from flask import request, jsonify
from database import db, ToDoTask
from . import api_bp

@api_bp.route('/tasks', methods=['GET', 'POST'])
def api_tasks():
    if request.method == 'GET':
        tasks = ToDoTask.query.all()
        return jsonify([{
            "task_id": t.task_id,
            "title": t.title,
            "description": t.description,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "dead_line": t.dead_line.isoformat() if t.dead_line else None,
            "creater": t.creater,
            "state": t.state
        } for t in tasks])
    
    data = request.get_json()
    task = ToDoTask(
        title=data['title'],
        description=data['description'],
        dead_line=data['dead_line'],
        creater=data['creater'],
        state=data.get('state', 1)
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({"task_id": task.task_id}), 201

@api_bp.route('/tasks/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_task(id):
    task = ToDoTask.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "dead_line": task.dead_line.isoformat() if task.dead_line else None,
            "creater": task.creater,
            "state": task.state
        })
    elif request.method == 'PUT':
        data = request.get_json()
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        task.dead_line = data.get('dead_line', task.dead_line)
        task.state = data.get('state', task.state)
        db.session.commit()
        return jsonify({"task_id": task.task_id})
    elif request.method == 'DELETE':
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": "Deleted"})