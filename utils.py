import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_picture(file):
    """Save uploaded profile picture and return the URL path."""
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
    # Create unique filename
    ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    
    upload_path = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_path, exist_ok=True)
    
    filepath = os.path.join(upload_path, filename)
    file.save(filepath)
    
    return f"/static/uploads/profiles/{filename}"

def get_profile_picture_url(user):
    """Get profile picture URL or default."""
    if user and user.profil_pic_url and user.profil_pic_url.strip():
        return user.profil_pic_url
    return "/static/uploads/profiles/default.png"

def delete_old_picture(pic_url):
    """Delete old profile picture file if it's not the default."""
    if not pic_url or pic_url == "/static/uploads/profiles/default.png":
        return
    
    try:
        # Extract filename from URL
        filename = pic_url.split('/')[-1]
        if filename == 'default.png':
            return
        
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass