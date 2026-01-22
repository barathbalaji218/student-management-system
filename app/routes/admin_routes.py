from flask import Blueprint, request, redirect, flash, render_template, url_for
from app.decorators import login_required, admin_required
from app.db import db
from bson.objectid import ObjectId
from bson.errors import InvalidId

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@admin_required
def admin_dashboard():
    total_students = db.users.count_documents({"role": "student"})
    blocked_students = db.users.count_documents({
        "role": "student",
        "is_blocked": True
    })
    total_subjects = db.subjects.count_documents({})
    total_leaves = db.leave_request.count_documents({})

    return render_template("admin/dashboard.html",
        total_students= total_students,
        blocked_students= blocked_students,
        total_subjects= total_subjects,
        total_leaves=total_leaves
    )

@admin_bp.route("/student")
@login_required
@admin_required
def view_student():
    status = request.args.get("status")
    query = {"role": "student"}
    if status == 'blocked':
        query['is_blocked'] = True

    students = list(db.users.find(query))
    return render_template("admin/students.html", students=students)

    # output = ""
    # for student in students:
    #     output += f"""
    # <p>
    #     Name: {student['name']} |
    #     Email: {student['email']} |
    #     Blocked: {student['is_blocked']} |
    #     <a href="/admin/student/{student['_id']}">View </a> |
    #     <a href="/admin/toggle-block/{student['_id']}">Block/Unblock</a> |
    #     <a href="/admin/delete-student/{student['_id']}">Delete</a>
    # </p>
    # """
    # return output or "No student found"

@admin_bp.route('/student/<student_id>')
@login_required
@admin_required
def student_detail(student_id):
    student = db.users.find_one({
        "_id": ObjectId(student_id)
    })

    if not student: 
        flash("Student not found", "danger")
        return redirect(url_for("admin.vew_student"))
    
    marks = list(db.marks.aggregate([
        {"$match": {"student_id": ObjectId(student_id)}},
        {
            "$lookup":{
                "from": "subjects",
                "localField": "subject_id",
                "foreignField": "_id",
                "as": "subject"
            }
        },
        {"$unwind": "$subject"}
    ]))

    return render_template("admin/student_detail.html", student= student, marks=marks)
    # return f"""
    # <h2>Student Details</h2>
    # <p>Name: {student['name']}</p>
    # <p>Email: {student['email']}</p>
    # <p>Phone: {student['phone']}</p>
    # <p>Blocked : {student['is_blocked']}</p>
    # """


# Block student
@admin_bp.route('/toggle-block/<student_id>')
@login_required
@admin_required
def toggle_block(student_id):
    student = db.users.find_one({"_id": ObjectId(student_id)})

    if not student: 
        flash("Student not found","danger")
        return redirect(url_for('admin.view_student'))

    db.users.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": {"is_blocked": not student['is_blocked']}}
    )

    status  = "blocked" if not student['is_blocked'] else "unblocked"
    flash(f"Student {student['name']} profile has been successfully {status}", "success")

    return redirect(url_for("admin.view_student"))
    # return "Student block status update"

# Delete Student
@admin_bp.route('/delete-student/<student_id>')
@login_required
@admin_required
def delete_student(student_id):
    student = db.users.find_one({"_id": ObjectId(student_id)})

    if not student:
        flash("Student not found", "danger")
        return redirect(url_for("admin.view_student"))

    db.users.delete_one({"_id": ObjectId(student_id)})
    flash("Student deleted successfully", "danger")
    
    return redirect(url_for("admin.view_student")) 


@admin_bp.route('/add-subject', methods=['GET', 'POST'])
@login_required
@admin_required
def add_subject():
    if request.method == 'POST':
        subject_name = request.form.get('subject_name')

        if not subject_name:
            flash("Subject name is required", "danger")
            return redirect(url_for('admin.add_subject'))
        
        existing = db.subjects.find_one({
            "subject_name": {"$regex": f"^{subject_name}$", "$options":"i"}
        })

        if existing:
            flash("Subject already exists", "warning")
            return redirect('/admin/add-subject')

        db.subjects.insert_one({"subject_name": subject_name})
        flash("Subject added successfully", "success")
        return redirect('/admin/subjects')
    
    return render_template("admin/add_subject.html")

    # return """
    # <h2> Add Subject </h2>
    # <form method="post">
    #     <input name= "subject_name" placeholder="Subject Name">
    #     <button type= "submit">Submit</button>
    # </form>
    # """

@admin_bp.route('/subjects')
@login_required
@admin_required
def view_subject():
    subjects = list(db.subjects.find())
    return render_template("admin/subjects.html", subjects=subjects)

@admin_bp.route('/delete-subject/<subject_id>', methods=['POST'])
@login_required
@admin_required
def delete_subject(subject_id):
    db.subjects.delete_one({"_id": ObjectId(subject_id)})
    flash("Subject deleted successfully", "success")
    return redirect('/admin/subjects')


@admin_bp.route('/add-marks/<student_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def add_marks(student_id):
    try:
        student_id = ObjectId(student_id)
    except InvalidId:
        flash("Invalid ID", "danger")
        return redirect(url_for("admin.dashboard"))

    # Subjects already graded
    graded_subjects = db.marks.distinct(
        "subject_id",
        {"student_id": student_id}
    )

    subjects = list(db.subjects.find(
        {
            "_id": {"$nin": graded_subjects}
        }
    ))

    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        marks = request.form.get('marks')

        if not subject_id or not marks:
            flash("All fields are required", "danger")
            return redirect(request.url)

        existing_mark = db.marks.find_one({
            "student_id": student_id,
            "subject_id": ObjectId(subject_id)
        })

        if existing_mark:
            flash("Marks already exist for this subject", "warning")
            return redirect(request.url)

        db.marks.insert_one({
            "student_id": ObjectId(student_id),
            "subject_id": ObjectId(subject_id),
            "marks": int(marks)
        })

        flash("Student marks added successfully", "success")
        return redirect(url_for('admin.student_detail', student_id=student_id))

    return render_template(
        "admin/add_marks.html",
        subjects=subjects,
        student_id=student_id
    )

    # form = "<h2>Add Marks</h2><form method='POST'>"  
    # form += "<select name='subject_id'>"

    # for subject in subjects:
    #     form+= f"<option value='{subject['_id']}'>{subject['subject_name']}</option>" 

    # form += "</select><br><br>"
    # form += "<input name='marks' placeholder='Marks'><br><br>"
    # form += "<button type = 'submit'>Submit</button></form>"
    # flash("Student marks added succesfully", "sucess")

    # return form


@admin_bp.route('/edit-marks/<mark_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_marks(mark_id):
    mark = db.marks.find_one({"_id": ObjectId(mark_id)})

    if not mark: 
        flash("Mark not found", "danger")
        return redirect('/admin/student')
    
    student_id = mark['student_id']
    subject = db.subjects.find_one({"_id": mark["subject_id"]})

    if request.method == 'POST': 
        new_marks = request.form.get('marks')

        if not new_marks:
            flash("Marks cannot be empty", "danger")
            return redirect(request.url)
    
        db.marks.update_one(
            {"_id": ObjectId(mark_id)},
            {"$set": {"marks": int(new_marks)}}
        )

        flash("Student marks updated succesfully", "success")
        return redirect(url_for('admin.student_detail', student_id=student_id))
    
    return render_template(
        "admin/edit_marks.html",
        mark=mark,
        subject=subject
    )
    # return f"""
    # <h2>Edit Marks</h2>
    # <p>Subject: {subject["subject_name"]}</p>
    # <form method="post">
    #     <input name="mark" value="{mark['marks']}">
    #     <button type="submit">Update</button>
    # </form>
    # """



@admin_bp.route('/leave-requests')
@login_required
@admin_required
def view_leave_request():
    leaves = list(db.leave_request.find().sort("created_at", -1))


    for leave in leaves:
        student = db.users.find_one({"_id": leave["student_id"]})
        leave["student_name"] = student["name"] if student else "Unknown"
        
    return render_template("admin/leave_requests.html", leaves=leaves)



@admin_bp.route('/leave/<leave_id>')
@login_required
@admin_required
def view_leave(leave_id):
    leave = db.leave_request.find_one({"_id": ObjectId(leave_id)})

    if not leave:
        flash("Leave request not found", "danger")
        return redirect(url_for("admin.view_leave_request"))
    
    student = db.users.find_one({"_id": leave['student_id']})

    return render_template("admin/leave_detail.html", leave=leave, student=student)

    # return f"""
    # <h2>Leave Request</h2>
    # <p>Student : {student['name']}</p>
    # <p>Reason : {leave['reason']}</p>  
    # <p>From_date : {leave['from_date']}</p>
    # <p>To : {leave['to_date']}</p>
    # <p>Status : {leave['status']}</p>

    # <form method='post' action='/admin/leave/approve/{leave['_id']}'>
    #     <input name="remark" placeholder="Approval remark">
    #     <button type="submit">Approve</button>
    # </form>

    # <form method="post" action="/admin/leave/reject/{leave['_id']}">
    #     <input name="remark" placeholder="Rejection reason">
    #     <button type="submit">Reject</button>
    # </form>
    # """


@admin_bp.route('/leave/approve/<leave_id>', methods=['POST'])
@login_required
@admin_required
def approve_leave(leave_id):
    db.leave_request.update_one(
        {'_id': ObjectId(leave_id)},
        {
            "$set":{
                "status": "approved",
                "admin_remark": request.form.get("remark","")
            }
        }
    )
    flash("Leave request has been Approved", "success")
    return redirect(url_for('admin.view_leave_request'))


@admin_bp.route('/leave/reject/<leave_id>', methods=['POST'])
@login_required
@admin_required
def reject_leave(leave_id):
    db.leave_request.update_one(
        {'_id': ObjectId(leave_id)},
        {
            "$set":{
                "status": "rejected",
                "admin_remark": request.form.get("remark","")
            }
        }
    )
    flash("leave request has been Rejected", "success")

    return redirect(url_for('admin.view_leave_request'))