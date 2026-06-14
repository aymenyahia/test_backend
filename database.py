from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class UserRole(db.Model):
    __tablename__ = 'user_roles'
    user_role_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role = db.Column(db.Text, nullable=False)

class Grade(db.Model):
    __tablename__ = 'grades'
    grade_id = db.Column(db.Integer, primary_key=True)
    grade_name = db.Column(db.Text, nullable=False)

class Category(db.Model):
    __tablename__ = 'categories'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.Text, nullable=False)

class User(db.Model):
    __tablename__ = 'users'
    matricule = db.Column(db.Text, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    family_name = db.Column(db.Text, nullable=False)
    category = db.Column(db.Integer, db.ForeignKey('categories.category_id'), nullable=False)
    grade = db.Column(db.Integer, db.ForeignKey('grades.grade_id'), nullable=False)
    user_name = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    profil_pic_url = db.Column(db.Text, nullable=False)
    user_role = db.Column(db.Integer, db.ForeignKey('user_roles.user_role_id'), nullable=False)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)  # NEW: Approval status
    
    category_rel = db.relationship('Category', backref='users')
    grade_rel = db.relationship('Grade', backref='users')
    role_rel = db.relationship('UserRole', backref='users')
    approval_request = db.relationship('UserApprovalRequest', uselist=False, backref='user', cascade='all, delete-orphan')

# NEW: Model for tracking user approval requests
class UserApprovalRequest(db.Model):
    __tablename__ = 'user_approval_requests'
    request_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_matricule = db.Column(db.Text, db.ForeignKey('users.matricule'), nullable=False, unique=True)
    requested_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    rejection_reason = db.Column(db.Text, nullable=True)

# ... rest of models stay the same ...
class TaskState(db.Model):
    __tablename__ = 'task_states'
    task_state_id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.Text, nullable=False)

class ToDoTask(db.Model):
    __tablename__ = 'ToDo_task'
    task_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    dead_line = db.Column(db.DateTime, nullable=False)
    creater = db.Column(db.Text, db.ForeignKey('users.matricule'), nullable=False)
    state = db.Column(db.Integer, db.ForeignKey('task_states.task_state_id'), nullable=False)
    
    creator_rel = db.relationship('User', backref='tasks')
    state_rel = db.relationship('TaskState', backref='tasks')

class Assignment(db.Model):
    __tablename__ = 'assignement'
    assignement_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Text, db.ForeignKey('users.matricule'), nullable=False)
    task_id = db.Column(db.Text, db.ForeignKey('ToDo_task.task_id'), nullable=False)
    
    user = db.relationship('User', backref='assignments')
    task = db.relationship('ToDoTask', backref='assignments')

class P2PChat(db.Model):
    __tablename__ = 'p2p_chat'
    p2p_id = db.Column(db.Integer, primary_key=True)
    first_user = db.Column(db.Text, db.ForeignKey('users.matricule'), nullable=False)
    second_user = db.Column(db.Text, db.ForeignKey('users.matricule'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    first_user_rel = db.relationship('User', foreign_keys=[first_user], backref='p2p_chats_first')
    second_user_rel = db.relationship('User', foreign_keys=[second_user], backref='p2p_chats_second')

class P2PMessage(db.Model):
    __tablename__ = 'p2p_message'
    p2p_message_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Text, db.ForeignKey('users.matricule'), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('p2p_chat.p2p_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship('User', backref='p2p_messages')
    chat = db.relationship('P2PChat', backref='messages')

class GroupChat(db.Model):
    __tablename__ = 'group_chat'
    group_chat_id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    task_id = db.Column(db.Integer, db.ForeignKey('ToDo_task.task_id'), nullable=True)
    profil_pic_url = db.Column(db.Text, nullable=False)
    
    task = db.relationship('ToDoTask', backref='group_chats')

class GroupChatMembership(db.Model):
    __tablename__ = 'group_chat_membership'
    group_chat_membership_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Text, db.ForeignKey('users.matricule'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group_chat.group_chat_id'), nullable=False)
    is_creater = db.Column(db.Integer, nullable=False)
    
    user = db.relationship('User', backref='group_memberships')
    group = db.relationship('GroupChat', backref='memberships')

class GroupMessage(db.Model):
    __tablename__ = 'group_message'
    group_message_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Text, db.ForeignKey('users.matricule'), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('group_chat.group_chat_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship('User', backref='group_messages')
    chat = db.relationship('GroupChat', backref='messages')

class P2PFile(db.Model):
    __tablename__ = 'p2p_files'
    p2p_file_id = db.Column(db.Integer, primary_key=True)
    creater = db.Column(db.Text, db.ForeignKey('users.matricule'), nullable=False)
    url = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    chat_id = db.Column(db.Integer, db.ForeignKey('p2p_chat.p2p_id'), nullable=False)
    
    creator = db.relationship('User', backref='p2p_files')
    chat = db.relationship('P2PChat', backref='files')

class GroupFile(db.Model):
    __tablename__ = 'group_files'
    group_file_id = db.Column(db.Integer, primary_key=True)
    creater = db.Column(db.Text, db.ForeignKey('users.matricule'), nullable=False)
    url = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    chat_id = db.Column(db.Integer, db.ForeignKey('group_chat.group_chat_id'), nullable=False)
    
    creator = db.relationship('User', backref='group_files')
    chat = db.relationship('GroupChat', backref='files')