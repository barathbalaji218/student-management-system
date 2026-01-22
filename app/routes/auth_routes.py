from flask import Blueprint, request, redirect, url_for, session, render_template, flash
from app.db import db
from app.utils import hash_password, verify_password

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_phone = request.form['email_or_phone']
        password  = request.form['password']

        user = db.users.find_one({
            "$or": [
                {"email": email_or_phone},
                {"phone": email_or_phone}
            ]
        })

        if user and verify_password(user['password'], password):
            if user.get('is_blocked'):
                return "User is blocked"
            
            session['user_id'] = str(user['_id'])
            session['role'] = user['role']

            if user['role'] == 'admin':
                flash(f"Login Suceesfull, Welcome back {user['name']}!", "success")
                return redirect(url_for('admin.admin_dashboard'))
            else: 
                flash(f"Welcome back {user['name']}!", "success")
                return redirect(url_for('student.student_dashboard'))
                
        flash("Invalid email or password", "danger")
        return redirect(url_for('auth.login'))

    return render_template('auth/login.html')

    # return """
    # <h2>Login</h2>
    # <form method="post">
    #     <input name="email_or_phone" placeholder="Email or Phone"><br><br>
    #     <input name="password" type="password" placeholder="Password"><br><br>
    #     <button type="submit">Login</button>
    # </form>
    # """

@auth_bp.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name  = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        print("phonenumlen: ", len(phone))
        if len(phone) < 10 or not phone.isdigit():
            flash("Phone number is invalid", "danger")
            return redirect(url_for("auth.register"))

        password = request.form.get('password')
        if len(password) < 8:
            flash("Password must be at least 8 characters", "danger")
            return redirect(request.url)
        confirm_password = request.form.get("confirm_password")
        
        if not all([name, email, phone, password, confirm_password]):
            flash("All fields are required", "danger")
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash("Password does not match", "danger")
            return redirect(url_for('auth.register'))
        
        if db.users.find_one({'email': email}):
            flash("Email already registered! Please login to your Account", "warning")
            return redirect(url_for('auth.login'))
        
        password_hash = hash_password(password)

        users = {
            "name" : name, 
            "email": email.strip().lower(),
            "phone": phone,
            "password": password_hash,   
            "role": "student",
            "is_blocked": False
        }

        db.users.insert_one(users)
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

    # return """'''
    # <h2>Student Register</h2>
    # <form method="post">
    #     <input name="name" placeholder="Name"><br><br>
    #     <input name="email" placeholder="Email"><br><br>
    #     <input name="phone" placeholder="Phone"><br><br>
    #     <input name="password" type="password" placeholder="Password"><br><br>
    #     <button type="submit">Register</button>
    # </form>
    # '''"""

@auth_bp.route("/test-db")
def test_db():
    users = db.users.find()
    return f"Users collection found. Count: {len(list(users))}"

@auth_bp.route("/create-admin")
def create_admin():
    admin = {
        "name": "Admin",
        "email": "admin@gmail.com",
        "phone": "999999999",
        "password": hash_password("admin123"),
        "role": "admin",
        "is_blocked": False 
    }

    db.users.insert_one(admin)
    return "Admin User Created!"


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))