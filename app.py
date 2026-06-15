import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from sqlalchemy import text
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from database import db, Grade, Category, User, TaskState, ToDoTask, Assignment, UserRole, UserApprovalRequest
from database import P2PChat, P2PMessage, GroupChat, GroupChatMembership
from database import GroupMessage, P2PFile, GroupFile
from api import api_bp
from auth import login_required, role_required, admin_required, manager_required, get_current_user, ROLE_ADMIN, ROLE_MANAGER, ROLE_USER
from utils import save_profile_picture, get_profile_picture_url, delete_old_picture

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
app.register_blueprint(api_bp)

# Serve uploaded files
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.context_processor
def inject_pending_approvals_count():
    """Make pending approvals count available in all templates"""
    def get_pending_approvals_count():
        return UserApprovalRequest.query.count()
    return dict(get_pending_approvals_count=get_pending_approvals_count)

@app.context_processor
def inject_user_profile_pic():
    """Make current user's profile picture available in all templates"""
    def get_user_profile_pic():
        if 'user_matricule' in session:
            user = User.query.get(session['user_matricule'])
            if user:
                return get_profile_picture_url(user)
        return '/static/uploads/profiles/default.png'
    return dict(profile_pic=get_user_profile_pic())

# ============================================================
# LOGIN / AUTH ROUTES
# ============================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_matricule' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(user_name=username).first()
        
        # Check if user exists, password is correct, AND user is approved
        if user and check_password_hash(user.password, password):
            if not user.is_approved:
                flash('Your account is pending admin approval. Please wait for approval.', 'warning')
                return render_template('login.html')
            
            session['user_matricule'] = user.matricule
            session['user_name'] = user.name
            session['user_role'] = user.user_role
            session['user_role_name'] = user.role_rel.role if user.role_rel else 'Unknown'
            flash(f'Welcome, {user.name} {user.family_name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_matricule' in session:
        return redirect(url_for('dashboard'))
    
    grades = Grade.query.all()
    categories = Category.query.all()
    
    if request.method == 'POST':
        matricule = request.form.get('matricule')
        name = request.form.get('name')
        family_name = request.form.get('family_name')
        category = request.form.get('category')
        grade = request.form.get('grade')
        user_name = request.form.get('user_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('signup.html', grades=grades, categories=categories)
        
        if User.query.filter_by(matricule=matricule).first():
            flash('Matricule already exists', 'danger')
            return render_template('signup.html', grades=grades, categories=categories)
        
        if User.query.filter_by(user_name=user_name).first():
            flash('Username already taken', 'danger')
            return render_template('signup.html', grades=grades, categories=categories)
        
        # Handle profile picture upload
        pic_url = ""
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            saved_path = save_profile_picture(file)
            if saved_path:
                pic_url = saved_path
        
        # Create user with is_approved=False (NEW)
        user = User(
            matricule=matricule,
            name=name,
            family_name=family_name,
            category=category,
            grade=grade,
            user_name=user_name,
            password=generate_password_hash(password),
            profil_pic_url=pic_url,
            user_role=ROLE_USER,
            is_approved=False  # NEW: Set to unapproved by default
        )
        db.session.add(user)
        db.session.flush()  # Flush to get the user in the session
        
        # Create approval request (NEW)
        approval_request = UserApprovalRequest(user_matricule=matricule)
        db.session.add(approval_request)
        db.session.commit()
        
        flash('Account created successfully! Your account is pending admin approval. Please wait for an admin or manager to approve it.', 'info')
        return redirect(url_for('login'))
    
    return render_template('signup.html', grades=grades, categories=categories)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(user_name=username).first()
    
    if user and check_password_hash(user.password, password):
        # Check if user is approved (NEW)
        if not user.is_approved:
            return jsonify({"error": "Your account is pending admin approval"}), 403
        
        session['user_matricule'] = user.matricule
        session['user_name'] = user.name
        session['user_role'] = user.user_role
        session['user_role_name'] = user.role_rel.role if user.role_rel else 'Unknown'
        return jsonify({
            "matricule": user.matricule,
            "name": user.name,
            "family_name": user.family_name,
            "user_name": user.user_name,
            "role": user.role_rel.role if user.role_rel else 'Unknown',
            "role_id": user.user_role,
            "profile_pic": get_profile_picture_url(user)
        })
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json()
    
    if User.query.filter_by(matricule=data.get('matricule')).first():
        return jsonify({"error": "Matricule already exists"}), 409
    
    if User.query.filter_by(user_name=data.get('user_name')).first():
        return jsonify({"error": "Username already taken"}), 409
    
    # Create user with is_approved=False (NEW)
    user = User(
        matricule=data['matricule'],
        name=data['name'],
        family_name=data['family_name'],
        category=data['category'],
        grade=data['grade'],
        user_name=data['user_name'],
        password=generate_password_hash(data['password']),
        profil_pic_url=data.get('profil_pic_url', ''),
        user_role=ROLE_USER,
        is_approved=False  # NEW: Set to unapproved by default
    )
    db.session.add(user)
    db.session.flush()
    
    # Create approval request (NEW)
    approval_request = UserApprovalRequest(user_matricule=data['matricule'])
    db.session.add(approval_request)
    db.session.commit()
    
    return jsonify({"matricule": user.matricule, "message": "Account created. Awaiting admin approval"}), 201

# ============================================================
# PROFILE ROUTES
# ============================================================

@app.route('/profile')
@login_required
def profile():
    user = get_current_user()
    pic_url = get_profile_picture_url(user)
    return render_template('profile.html', user=user, profile_pic=pic_url)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = get_current_user()
    
    if request.method == 'POST':
        # Update basic info
        user.name = request.form.get('name', user.name)
        user.family_name = request.form.get('family_name', user.family_name)
        user.user_name = request.form.get('user_name', user.user_name)
        
        # Update password if provided
        new_password = request.form.get('new_password')
        if new_password:
            confirm_password = request.form.get('confirm_password')
            if new_password != confirm_password:
                flash('Passwords do not match', 'danger')
                return redirect(url_for('edit_profile'))
            user.password = generate_password_hash(new_password)
        
        # Handle profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '':
                saved_path = save_profile_picture(file)
                if saved_path:
                    # Delete old picture
                    delete_old_picture(user.profil_pic_url)
                    user.profil_pic_url = saved_path
        
        db.session.commit()
        # Update session
        session['user_name'] = user.name
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    
    pic_url = get_profile_picture_url(user)
    return render_template('edit_profile.html', user=user, profile_pic=pic_url)

@app.route('/api/profile', methods=['GET', 'PUT'])
@login_required
def api_profile():
    user = get_current_user()
    
    if request.method == 'GET':
        return jsonify({
            "matricule": user.matricule,
            "name": user.name,
            "family_name": user.family_name,
            "user_name": user.user_name,
            "category": user.category,
            "grade": user.grade,
            "profil_pic_url": get_profile_picture_url(user),
            "role": user.role_rel.role if user.role_rel else None
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        user.name = data.get('name', user.name)
        user.family_name = data.get('family_name', user.family_name)
        user.user_name = data.get('user_name', user.user_name)
        if 'password' in data and data['password']:
            user.password = generate_password_hash(data['password'])
        db.session.commit()
        return jsonify({"message": "Profile updated"})

# ============================================================
# WEB INTERFACE ROUTES (PROTECTED)
# ============================================================

@app.route('/')
@login_required
def dashboard():
    user = get_current_user()
    stats = {
        'users_count': User.query.count(), 'tasks_count': ToDoTask.query.count(),
        'grades_count': Grade.query.count(), 'categories_count': Category.query.count(),
        'p2p_chats_count': P2PChat.query.count(), 'group_chats_count': GroupChat.query.count()
    }
    return render_template('dashboard.html', stats=stats, user=user, profile_pic=get_profile_picture_url(user))


# --- USERS (Admin only) ---
@app.route('/web/users')
@manager_required
def web_users():
    users = User.query.all()
    grades = Grade.query.all()
    categories = Category.query.all()
    roles = UserRole.query.all()
    return render_template('tables/users.html', users=users, grades=grades, categories=categories, roles=roles)

@app.route('/web/users/add', methods=['POST'])
@manager_required
def web_add_user():
    profile_pic = 'default.png'
    if 'profil_pic' in request.files:  # Note: profil_pic (with 'l')
        file = request.files['profil_pic']
        if file and file.filename:  # Check file exists and has name
            saved = save_profile_picture(file)
            if saved: 
                profile_pic = saved
    
    db.session.add(User(
        matricule=request.form['matricule'],
        name=request.form['name'],
        family_name=request.form['family_name'],
        category=request.form['category'],
        grade=request.form.get('grade', "بدون رتبة"),
        user_name=request.form['user_name'],
        password=generate_password_hash(request.form['password']),
        profil_pic_url=profile_pic,
        user_role=request.form.get('user_role', ROLE_USER),
        is_approved=True  # Admin-added users are automatically approved
    ))
    db.session.commit()
    flash('User added', 'success')
    return redirect(url_for('web_users'))

@app.route('/web/users/edit', methods=['POST'])
@manager_required
def web_edit_user():
    matricule = request.form['matricule']
    user = User.query.get_or_404(matricule)
    
    current_role = session.get('user_role', ROLE_USER)
    target_role = user.user_role
    
    # Can edit same role or lower (higher number = lower privilege)
    if current_role > target_role:
        flash('You cannot modify this user', 'danger')
        return redirect(url_for('web_users'))
    
    # Update allowed fields only
    user.name = request.form.get('name', user.name)
    user.family_name = request.form.get('family_name', user.family_name)
    user.category = request.form.get('category', user.category)
    user.grade = request.form.get('grade', user.grade)
    
    # Role change: can only assign same role or lower
    new_role = request.form.get('user_role')
    if new_role:
        new_role_int = int(new_role)
        if new_role_int < current_role:
            flash('You cannot assign a higher privilege role', 'danger')
            return redirect(url_for('web_users'))
        user.user_role = new_role_int
    
    db.session.commit()
    flash('User updated successfully', 'success')
    return redirect(url_for('web_users'))

@app.route('/web/users/delete/<matricule>')
@admin_required
def web_delete_user(matricule):
    user = User.query.get_or_404(matricule)
    if user.profil_pic_url and user.profil_pic_url != 'default.png':
        pic_path = os.path.join(app.config['UPLOAD_FOLDER'], user.profil_pic_url)
        if os.path.exists(pic_path): os.remove(pic_path)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted', 'success')
    return redirect(url_for('web_users'))

# --- USER APPROVALS (Admin/Manager) ---
@app.route('/web/pending-approvals')
@manager_required
def web_pending_approvals():
    """Display all pending user approval requests"""
    pending_requests = UserApprovalRequest.query.all()
    return render_template('tables/pending_approvals.html', pending_requests=pending_requests)

@app.route('/web/approve-user/<matricule>', methods=['POST'])
@manager_required
def web_approve_user(matricule):
    """Approve a pending user"""
    user = User.query.get_or_404(matricule)
    
    if user.is_approved:
        flash('User is already approved', 'warning')
        return redirect(url_for('web_pending_approvals'))
    
    # Approve the user
    user.is_approved = True
    
    # Delete the approval request
    approval_request = UserApprovalRequest.query.filter_by(user_matricule=matricule).first()
    if approval_request:
        db.session.delete(approval_request)
    
    db.session.commit()
    flash(f'User {user.name} {user.family_name} has been approved!', 'success')
    return redirect(url_for('web_pending_approvals'))

@app.route('/web/reject-user/<matricule>', methods=['POST'])
@manager_required
def web_reject_user(matricule):
    """Reject and delete a pending user"""
    user = User.query.get_or_404(matricule)
    
    # Delete profile picture if exists
    if user.profil_pic_url and user.profil_pic_url != 'default.png':
        pic_path = os.path.join(app.config['UPLOAD_FOLDER'], user.profil_pic_url)
        if os.path.exists(pic_path):
            os.remove(pic_path)
    
    # Delete approval request if exists
    approval_request = UserApprovalRequest.query.filter_by(user_matricule=matricule).first()
    if approval_request:
        db.session.delete(approval_request)
    
    # Delete the user
    user_name = f"{user.name} {user.family_name}"
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user_name} has been rejected and removed', 'warning')
    return redirect(url_for('web_pending_approvals'))

# --- GRADES (Admin/Manager) ---
@app.route('/web/grades')
@manager_required
def web_grades():
    grades = Grade.query.all()
    categories = Category.query.all()  # ADD THIS
    return render_template('tables/grades.html', grades=grades, categories=categories)

@app.route('/web/grades/add', methods=['POST'])
@manager_required
def web_add_grade():
    db.session.add(Grade(
        grade_name=request.form['grade_name'],
        category_id=request.form.get('category_id', 1)  # ADD THIS
    ))
    db.session.commit()
    flash('Grade added', 'success')
    return redirect(url_for('web_grades'))

@app.route('/web/grades/delete/<int:id>')
@manager_required
def web_delete_grade(id):
    db.session.delete(Grade.query.get_or_404(id))
    db.session.commit()
    flash('Grade deleted', 'success')
    return redirect(url_for('web_grades'))

# --- CATEGORIES (Admin/Manager) ---
@app.route('/web/categories')
@manager_required
def web_categories():
    categories = Category.query.all()
    return render_template('tables/categories.html', categories=categories)

@app.route('/web/categories/add', methods=['POST'])
@manager_required
def web_add_category():
    db.session.add(Category(category_name=request.form['category_name']))
    db.session.commit()
    flash('Category added', 'success')
    return redirect(url_for('web_categories'))

@app.route('/web/categories/delete/<int:id>')
@manager_required
def web_delete_category(id):
    db.session.delete(Category.query.get_or_404(id))
    db.session.commit()
    flash('Category deleted', 'success')
    return redirect(url_for('web_categories'))

# --- TASKS (All logged-in users) ---
@app.route('/web/tasks')
@login_required
def web_tasks():
    user = get_current_user()
    if user.user_role == ROLE_USER:
        tasks = ToDoTask.query.join(Assignment).filter(Assignment.user_id == user.matricule).all()
    else:
        tasks = ToDoTask.query.all()
    users = User.query.all()
    states = TaskState.query.all()
    return render_template('tables/tasks.html', tasks=tasks, users=users, states=states, user=user)

@app.route('/web/tasks/add', methods=['POST'])
@manager_required
def web_add_task():
    db.session.add(ToDoTask(
        title=request.form['title'], description=request.form['description'],
        dead_line=datetime.fromisoformat(request.form['dead_line']),
        creater=request.form['creater'], state=request.form.get('state', 1)
    ))
    db.session.commit()
    flash('Task added', 'success')
    return redirect(url_for('web_tasks'))

@app.route('/web/tasks/delete/<int:id>')
@manager_required
def web_delete_task(id):
    db.session.delete(ToDoTask.query.get_or_404(id))
    db.session.commit()
    flash('Task deleted', 'success')
    return redirect(url_for('web_tasks'))

# --- ASSIGNMENTS (Admin/Manager) ---
@app.route('/web/assignments')
@manager_required
def web_assignments():
    assignments = Assignment.query.all()
    users = User.query.all()
    tasks = ToDoTask.query.all()
    return render_template('tables/assignments.html', assignments=assignments, users=users, tasks=tasks)

@app.route('/web/assignments/add', methods=['POST'])
@manager_required
def web_add_assignment():
    db.session.add(Assignment(user_id=request.form['user_id'], task_id=request.form['task_id']))
    db.session.commit()
    flash('Assignment added', 'success')
    return redirect(url_for('web_assignments'))

@app.route('/web/assignments/delete/<int:id>')
@manager_required
def web_delete_assignment(id):
    db.session.delete(Assignment.query.get_or_404(id))
    db.session.commit()
    flash('Assignment deleted', 'success')
    return redirect(url_for('web_assignments'))

# --- CHATS (All logged-in users) ---
@app.route('/web/p2p-chats')
@login_required
def web_p2p_chats():
    user = get_current_user()
    if user.user_role == ROLE_USER:
        chats = P2PChat.query.filter(
            db.or_(P2PChat.first_user == user.matricule, P2PChat.second_user == user.matricule)
        ).all()
    else:
        chats = P2PChat.query.all()
    users = User.query.all()
    return render_template('tables/p2p_chats.html', chats=chats, users=users, user=user)

@app.route('/web/p2p-chats/add', methods=['POST'])
@login_required
def web_add_p2p_chat():
    db.session.add(P2PChat(first_user=request.form['first_user'], second_user=request.form['second_user']))
    db.session.commit()
    flash('P2P Chat created', 'success')
    return redirect(url_for('web_p2p_chats'))

@app.route('/web/group-chats')
@login_required
def web_group_chats():
    chats = GroupChat.query.all()
    tasks = ToDoTask.query.all()
    return render_template('tables/group_chats.html', chats=chats, tasks=tasks)

@app.route('/web/group-chats/add', methods=['POST'])
@manager_required
def web_add_group_chat():
    db.session.add(GroupChat(
        task_id=request.form.get('task_id') or None,
        profil_pic_url=request.form.get('profil_pic_url', '')
    ))
    db.session.commit()
    flash('Group Chat created', 'success')
    return redirect(url_for('web_group_chats'))

# --- SQL EXECUTOR (Admin only) ---
@app.route('/web/sql')
@admin_required
def web_sql():
    return render_template('sql_executor.html')

@app.route('/web/sql/execute', methods=['POST'])
@admin_required
def web_sql_execute():
    query = request.form.get('query', '').strip()
    try:
        result = db.session.execute(text(query))
        db.session.commit()
        if query.upper().startswith('SELECT') or query.upper().startswith('PRAGMA'):
            rows = result.fetchall()
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in rows]
            flash(f'{len(data)} rows returned', 'success')
            return render_template('sql_executor.html', columns=columns, rows=data, query=query)
        flash(f'Rows affected: {result.rowcount}', 'success')
        return render_template('sql_executor.html', query=query)
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return render_template('sql_executor.html', query=query)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default roles
        if not UserRole.query.get(ROLE_ADMIN):
            db.session.add(UserRole(user_role_id=ROLE_ADMIN, role='admin'))
        if not UserRole.query.get(ROLE_MANAGER):
            db.session.add(UserRole(user_role_id=ROLE_MANAGER, role='manager'))
        if not UserRole.query.get(ROLE_USER):
            db.session.add(UserRole(user_role_id=ROLE_USER, role='user'))
        
        # Create default avatar if not exists
        import shutil
        default_avatar_path = os.path.join(Config.UPLOAD_FOLDER, 'default.png')
        if not os.path.exists(default_avatar_path):
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            # Create a simple default avatar or copy one
            # For now, we'll create a placeholder
            from PIL import Image, ImageDraw, ImageFont
            try:
                img = Image.new('RGB', (200, 200), color='#16213e')
                draw = ImageDraw.Draw(img)
                draw.ellipse([20, 20, 180, 180], fill='#0f3460', outline='#e94560', width=4)
                draw.text((100, 100), "👤", fill='#e94560', anchor='mm', font_size=80)
                img.save(default_avatar_path)
            except Exception:
                # If PIL not available, create empty file
                with open(default_avatar_path, 'wb') as f:
                    pass
        
        db.session.commit()
    
    print("=" * 50)
    print("Bureau Management Server")
    print("=" * 50)
    print("Running on: http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)