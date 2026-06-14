from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify

# Role constants
ROLE_ADMIN = 1
ROLE_MANAGER = 2
ROLE_USER = 3

def login_required(f):
    """Decorator to protect routes - requires login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_matricule' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required"}), 401
            flash('Please log in first', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Decorator to restrict routes by role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_matricule' not in session:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({"error": "Authentication required"}), 401
                flash('Please log in first', 'danger')
                return redirect(url_for('login'))
            
            user_role = session.get('user_role')
            if user_role not in allowed_roles:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({"error": "Insufficient permissions"}), 403
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Get current logged-in user info from session."""
    from database import User
    if 'user_matricule' in session:
        return User.query.get(session['user_matricule'])
    return None

# Convenience decorators
admin_required = role_required(ROLE_ADMIN)
manager_required = role_required(ROLE_ADMIN, ROLE_MANAGER)