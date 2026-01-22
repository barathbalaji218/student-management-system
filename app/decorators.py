from functools import wraps 
from flask import session, redirect, url_for

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session: 
            return redirect(url_for('auth.login'))
        return func(*args, **kwargs)
    return wrapper

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('role') != "admin":
            return redirect(url_for('auth.login'))
        return func(*args, **kwargs)
    return wrapper

def student_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('role') != "student":
            return redirect(url_for('auth.login'))
        return func(*args, **kwargs)
    return wrapper