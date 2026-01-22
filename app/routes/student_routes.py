from flask import Blueprint, session, request, redirect, render_template, flash
from app.decorators import login_required, student_required
from bson import ObjectId
from app.db import db
from datetime import datetime

student_bp = Blueprint("student", __name__, url_prefix="/student")

@student_bp.route("/dashboard")
@login_required
@student_required
def student_dashboard():
    student_id = ObjectId(session['user_id'])

    marks_cursor = db.marks.find({"student_id": student_id})
    mark_list = [m['marks'] for m in marks_cursor]

    if not mark_list:
        return render_template(
            "student/dashboard.html",
            total_subjects=0,
            avg_marks=0,
            highest_marks=0,
            lowest_marks=0
        )

    return render_template(
        "student/dashboard.html",
        total_subjects=len(mark_list),
        avg_marks=round(sum(mark_list)/len(mark_list), 2),
        highest_marks=max(mark_list),
        lowest_marks=min(mark_list)
    )
    # return f"""
    # <h2>Student Dashboard</h2>
    # <p>Total Subject : {len(mark_list)}</p>
    # <p>Average Marks : {sum(mark_list)/len(mark_list):.2f}</p>
    # <p>Highest Mark : {max(mark_list)}</p>
    # <p>Lowest Mark : {min(mark_list)}</p>
    # """


@student_bp.route('/marks')
@login_required
@student_required
def view_marks():
    student_id = ObjectId(session['user_id'])

    marks_cursor = db.marks.find({"student_id": student_id})
    marks_data = []

    for mark in marks_cursor:
        subject = db.subjects.find_one({"_id": mark["subject_id"]})
        marks_data.append({
            "subject": subject["subject_name"],
            "marks": mark["marks"]
        })

    return render_template("student/marks.html", marks=marks_data)

    

@student_bp.route('/leave-request', methods=['GET', 'POST'])
@login_required
@student_required
def leave_request():
    if request.method == 'POST':
        db.leave_request.insert_one({
            'student_id': ObjectId(session['user_id']),
            'reason': request.form.get('reason'),
            'from_date': request.form.get('from_date'),
            'to_date': request.form.get('to_date'),
            'status': "pending",
            "admin_remark": "",
            "created_at": datetime.utcnow() 
        })
        flash("Leave request submitted successfully", "success")
        return redirect('/student/leave-status')
    
    return render_template("student/leave_request.html")
    # return """
    # <h2>Submit leave Form</h2>
    #     <form method='POST'>
    #         <input name="reason" placeholder="Reason" required><br>
    #         <input type="date" name="from_date" required><br>
    #         <input type="date" name="to_date" required><br>
    #         <button type="submit">Submit</button>+
    #     </form>
    # """

@student_bp.route('/leave-status')
@login_required
@student_required
def leave_status():
    student_id = ObjectId(session['user_id'])

    leaves = list(db.leave_request.find(
        {"student_id": student_id},
    ).sort("created_at",-1))

    return render_template(
        "student/leave_status.html",
        leaves=leaves
    )


    # for leave in leaves:
    #     output +=f"""
    #     <p>
    #         Reason: {leave['reason']} |
    #         From: {leave['from_date']} |
    #         To: {leave['to_date']} |
    #         Status: {leave['status']} |
    #         Remark: {leave.get('admin_remark', '')} 
    #     </p>
    #     """
    # return output or "No leave requests found"