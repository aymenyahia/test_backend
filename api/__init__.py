from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from . import grades, categories, users, tasks, assignments, chats, messages, files, sql