from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    return generate_password_hash(password)

def verify_password(hash_password, password):
    return check_password_hash(hash_password, password)

def send_leave_status_email(email, status, remark):
    """
    Email sending logic will be added later
    """
    print(f"""
        EMAIL TO: {email}
        STATUS: {status}
        REMARK: {remark}
    """)
