from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['job_portal']
jobs_collection = db['jobs']
applicants_collection = db['applicants']
student_collection = db['students']

@app.route('/')
def home():
    message = "Welcome to Flask Template Rendering!"
    return render_template('Dashboard_page/dashboard.html', msg=message)

@app.route('/placement_dashboard')
def placement_dashboard():
    return render_template('placement/placement-dashboard.html')


@app.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if request.method == 'POST':
        job = {
            'title': request.form.get('job_title'),
            'company': request.form.get('company'),
            'location': request.form.get('location'),
            'job_type': request.form.get('job_type'),
            'experience': request.form.get('experience'),
            'salary': request.form.get('salary'),
            'deadline': request.form.get('deadline'),
            'description': request.form.get('description'),
            'education': request.form.getlist('education[]'),
            'requirements': request.form.getlist('requirement[]'),
            'benefits': request.form.getlist('benefit[]')
        }
        jobs_collection.insert_one(job)
        return render_template('placement/post-job.html', job=job)
    return render_template('placement/post-job.html')

@app.route('/jobs')
def jobs():
    all_jobs = list(jobs_collection.find({}, {'_id': 0}))
    return render_template('placement/job-list.html', jobs=all_jobs)

@app.route('/applicants')
def view_applicants():
    applicants = list(applicants_collection.find())
    return render_template('placement/applicant-list.html', applicants=applicants)


@app.route('/mark_status/<email>/<status>')
def mark_status(email, status):
    applicants_collection.update_one(
        {'email': email},
        {'$set': {'status': status}}
    )
    flash(f"Applicant {email} marked as {status}.")
    return redirect(url_for('view_applicants'))


@app.route('/delete_applicant/<email>')
def delete_applicant(email):
    applicants_collection.delete_one({'email': email})
    flash(f"Applicant {email} has been deleted.")
    return redirect(url_for('view_applicants'))


@app.route('/edit_applicant/<email>', methods=['GET', 'POST'])
def edit_applicant(email):
    applicant = applicants_collection.find_one({'email': email})
    if request.method == 'POST':
        updated_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'dob': request.form.get('dob'),
            'job_title': request.form.get('job_title'),
            'status': request.form.get('status')
        }
        applicants_collection.update_one({'email': email}, {'$set': updated_data})
        flash(f"Applicant {email} updated successfully.")
        return redirect(url_for('view_applicants'))

    return render_template('placement/edit-applicant.html', applicant=applicant)


@app.route('/follow_up_applicant/<email>')
def follow_up_applicant(email):
    flash(f"Follow-up initiated for {email}.")
    # Placeholder: Integrate follow-up logic (e.g., email/SMS)
    return redirect(url_for('view_applicants'))

@app.route('/apply/<job_title>', methods=['GET', 'POST'])
def apply_job(job_title):
    if request.method == 'POST':
        applicant_name = request.form.get('name')
        applicant_email = request.form.get('email')
        applicant_phone = request.form.get('phone')
        applicant_dob = request.form.get('dob')

        applicant_data = {
            'job_title': job_title,
            'name': applicant_name,
            'email': applicant_email,
            'phone': applicant_phone,
            'dob': applicant_dob
        }

        # Save applicant data to MongoDB
        applicants_collection.insert_one(applicant_data)

        flash(f"Thanks {applicant_name} for applying to {job_title}!")
        return redirect(url_for('jobs'))

    return render_template('placement/apply-job.html', job_title=job_title)

@app.route('/reports')
def reports():
    # Count total job posts
    total_jobs = jobs_collection.count_documents({})

    # Count applicants per job title
    job_application_counts = applicants_collection.aggregate([
        {"$group": {"_id": "$job_title", "total_applicants": {"$sum": 1}}},
        {"$sort": {"total_applicants": -1}}
    ])

    application_stats = list(job_application_counts)

    return render_template('placement/reports.html', total_jobs=total_jobs, application_stats=application_stats)

@app.route('/upload')
def upload_form():
    return render_template('Admin/upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if not file:
        return "No file uploaded."

    try:
        df = pd.read_csv(file) if file.filename.endswith('.csv') else pd.read_excel(file)
        data = df.to_dict(orient='records')
        student_collection.insert_many(data)
        return render_template('admin/upload.html')
    except Exception as e:
        return f"An error occurred: {e}"
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        contact = request.form.get('contact')
        batch_id = request.form.get('batch_id')

        try:
            batch_id = int(batch_id)
            contact=int(contact)  # Ensure Batch Id is an integer
        except ValueError:
            flash('Batch ID must be a number.')
            return render_template('student/student_login.html')

        student = student_collection.find_one({
            'My Contact': contact,
            'Batch Id': batch_id
        })

        if student:
            return redirect(url_for('jobs', name=student.get('Name')))
        else:
            flash('Invalid contact number or batch ID. Please try again.')
            return render_template('student/student_login.html')

    return render_template('student/student_login.html')

  
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
