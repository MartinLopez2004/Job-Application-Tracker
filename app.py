import os
from flask import Flask, render_template, request, redirect, url_for, flash
import json
from dotenv import load_dotenv
from db_connection import get_db_connection

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


# Dashboard page
@app.route('/')
def dashboard():
    connection = get_db_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        # Get statistics from MySQL
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM companies) AS total_companies,
                (SELECT COUNT(*) FROM jobs) AS total_jobs,
                (SELECT COUNT(*) FROM applications) AS total_applications,
                (SELECT COUNT(*) FROM contacts) AS total_contacts
        """)

        stats = cursor.fetchone()
        return render_template(
            'dashboard.html',
            stats=stats
        )

    finally:
        cursor.close()
        connection.close()



# Job Match page
@app.route('/job-match', methods=['GET', 'POST'])
def job_match():

    if request.method == 'POST':

        # Get skills submitted through the form
        skills = request.form.get('skills', '').strip()

        # Get all jobs and their requirements
        connection = get_db_connection()

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute("""
                SELECT
                    jobs.job_id,
                    jobs.job_title,
                    jobs.requirements,
                    companies.company_name
                FROM jobs
                LEFT JOIN companies
                    ON jobs.company_id = companies.company_id
            """)

            jobs = cursor.fetchall()

        finally:
            cursor.close()
            connection.close()

        # Convert the user's skills into a list
        user_skills = [
            skill.strip().lower()
            for skill in skills.split(',')
            if skill.strip()
        ]

        # Compare user skills with job requirements
        matching_jobs = []

        for job in jobs:

            requirements = job['requirements']

            # Skip jobs without requirements
            if not requirements:
                continue

            # Convert JSON text into a Python dictionary if needed
            if isinstance(requirements, str):
                requirements = json.loads(requirements)

            required_skills = requirements.get('required_skills', [])

            # Skip jobs without required skills
            if not required_skills:
                continue

            matched_skills = [
                skill for skill in required_skills
                if skill.lower() in user_skills
            ]

            missing_skills = [
                skill for skill in required_skills
                if skill.lower() not in user_skills
            ]

            match_percentage = (
                len(matched_skills) / len(required_skills)
            ) * 100

            matching_jobs.append({
                'job_title': job['job_title'],
                'company_name': job['company_name'],
                'match_percentage': round(match_percentage),
                'matched_skills': matched_skills,
                'missing_skills': missing_skills
            })

        # Rank jobs from highest match to lowest
        matching_jobs.sort(
            key=lambda job: job['match_percentage'],
            reverse=True
        )

        return render_template(
            'job_match.html',
            skills=skills,
            matching_jobs=matching_jobs
        )

    return render_template('job_match.html')


# Companies page - READ
@app.route('/companies')
def companies():
    connection = get_db_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        # Get all companies from MySQL
        cursor.execute("""
            SELECT company_id, company_name, industry,
                   website, city, state, notes
            FROM companies
            ORDER BY company_id
        """)

        companies = cursor.fetchall()
        return render_template(
            'companies.html',
            companies=companies
        )

    finally:
        cursor.close()
        connection.close()

# Contacts page - READ
@app.route('/contacts')
def contacts():
    connection = get_db_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        # Get all contacts with their company names
        cursor.execute("""
            SELECT
                contacts.contact_id,
                contacts.company_id,
                companies.company_name,
                contacts.first_name,
                contacts.last_name,
                contacts.email,
                contacts.phone,
                contacts.job_title,
                contacts.linkedin_url,
                contacts.notes
            FROM contacts
            INNER JOIN companies
                ON contacts.company_id = companies.company_id
            ORDER BY contacts.contact_id
        """)

        contacts = cursor.fetchall()

        # Get all companies for the Add Contact dropdown
        cursor.execute("""
            SELECT company_id, company_name
            FROM companies
            ORDER BY company_name
        """)

        companies = cursor.fetchall()

        return render_template(
            'contacts.html',
            contacts=contacts,
            companies=companies
        )

    finally:
        cursor.close()
        connection.close()


# Applications page - READ
@app.route('/applications')
def applications():
    connection = get_db_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        # Get all applications with their job and company information
        cursor.execute("""
            SELECT
                applications.application_id,
                applications.job_id,
                jobs.job_title,
                companies.company_name,
                applications.application_date,
                applications.status,
                applications.resume_version,
                applications.cover_letter_sent,
                applications.response_date,
                applications.interview_date,
                applications.notes,
                applications.interview_data
                FROM applications
                INNER JOIN jobs
                ON applications.job_id = jobs.job_id
                INNER JOIN companies
                ON jobs.company_id = companies.company_id
                ORDER BY applications.application_id
                    """)

        applications = cursor.fetchall()

        # Prepare interview JSON data for the Edit form
        for application in applications:
            interview_data = application['interview_data']

            if isinstance(interview_data, str):
                interview_data = json.loads(interview_data)

            if not interview_data:
                interview_data = {}

            application['feedback'] = interview_data.get('feedback') or ''
            application['next_steps'] = interview_data.get('next_steps') or ''
            application['interviewers_text'] = ', '.join(
                interview_data.get('interviewers', [])
            )
            application['interview_rounds_value'] = interview_data.get('interview_rounds')
            application['technical_questions_text'] = ', '.join(
                interview_data.get('technical_questions', [])
            )
            application['rating_value'] = interview_data.get('rating')

        # Get all jobs for the Add and Edit dropdowns
        cursor.execute("""
            SELECT job_id, job_title
            FROM jobs
            ORDER BY job_title
        """)

        jobs = cursor.fetchall()

        return render_template(
            'applications.html',
            applications=applications,
            jobs=jobs
        )

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


# Jobs page - READ
@app.route('/jobs')
def jobs():
    connection = get_db_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        # Get all jobs from MySQL
        cursor.execute("""
            SELECT
                jobs.job_id,
                companies.company_name,
                jobs.company_id,
                jobs.job_title,
                jobs.job_description,
                jobs.salary_min,
                jobs.salary_max,
                jobs.job_type,
                jobs.posting_url,
                jobs.date_posted,
                jobs.is_active,
                jobs.requirements
            FROM jobs
            INNER JOIN companies
                ON jobs.company_id = companies.company_id
            ORDER BY jobs.job_id
        """)
        jobs = cursor.fetchall()

        # Prepare JSON requirements for the Edit form
        for job in jobs:

            requirements = job['requirements']

            if isinstance(requirements, str):
                requirements = json.loads(requirements)

            if not requirements:
                requirements = {}

            job['required_skills_text'] = ', '.join(
                requirements.get('required_skills', [])
            )

            job['preferred_skills_text'] = ', '.join(
                requirements.get('preferred_skills', [])
            )

            job['education_text'] = requirements.get('education') or ''

            job['experience_years_value'] = (
                requirements.get('experience_years')
            )

            job['remote_option_value'] = requirements.get(
                'remote_option', False
            )

        cursor.execute("""
            SELECT company_id, company_name
            FROM companies
            ORDER BY company_name
        """)
        companies = cursor.fetchall()

        return render_template(
            'jobs.html',
            jobs=jobs,
            companies=companies
        )

    finally:
        cursor.close()
        connection.close()

  # CREATE - Add a new company
@app.route('/companies/add', methods=['POST'])
def add_companies():

    # Get information submitted through the HTML form
    company_name = request.form.get('company_name', '').strip()
    industry = request.form.get('industry', '').strip()
    website = request.form.get('website', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    notes = request.form.get('notes', '').strip()

    # Company name is required
    if not company_name:
        flash("Company name is required.")
        return redirect(url_for('companies'))

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        # Insert the new company into MySQL
        query = """
            INSERT INTO companies
            (company_name, industry, website, city, state, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        values = (
            company_name,
            industry or None,
            website or None,
            city or None,
            state or None,
            notes or None
        )

        cursor.execute(query, values)

        connection.commit()

        flash("Company added successfully!")

    except Exception as error:
        connection.rollback()
        flash(f"Error adding company: {error}")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('companies'))  

 # CREATE - Add a new Contact
@app.route('/contacts/add', methods=['POST'])
def add_contacts():

    # Get information submitted through the HTML form
    company_id = request.form.get('company_id', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    job_title = request.form.get('job_title', '').strip()
    linkedin_url = request.form.get('linkedin_url', '').strip()
    notes = request.form.get('notes', '').strip()

    # company id is required
    if not company_id:
        flash("company id is required.")
        return redirect(url_for('contacts'))

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        # Insert the new contact into MySQL
        query = """
            INSERT INTO contacts
            (company_id, first_name, last_name, email, phone, job_title, linkedin_url, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            company_id,
            first_name or None,
            last_name or None,
            email or None,
            phone or None,
            job_title or None,
	    linkedin_url or None,
            notes or None
        )

        cursor.execute(query, values)

        connection.commit()

        flash("Contact added successfully!")

    except Exception as error:
        connection.rollback()
        flash(f"Error adding contact: {error}")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('contacts')) 

 # CREATE - Add a new application
@app.route('/applications/add', methods=['POST'])
def add_applications():

    # Get information submitted through the HTML form
    job_id = request.form.get('job_id', '').strip()
    application_date= request.form.get('application_date', '').strip()
    status = request.form.get('status', '').strip()
    resume_version = request.form.get('resume_version', '').strip()
    cover_letter_sent = request.form.get('cover_letter_sent', '').strip()
    response_date = request.form.get('response_date', '').strip()
    interview_date = request.form.get('interview_date', '').strip()
    notes = request.form.get('notes', '').strip()
    # Get interview information
    feedback = request.form.get('feedback', '').strip()
    next_steps = request.form.get('next_steps', '').strip()
    interviewers = request.form.get('interviewers', '').strip()
    interview_rounds = request.form.get('interview_rounds', '').strip()
    technical_questions = request.form.get('technical_questions', '').strip()
    rating = request.form.get('rating', '').strip()

    # Build interview information JSON
    interview_data = {
    'feedback': feedback or None,
    'next_steps': next_steps or None,
    'interviewers': [
        name.strip()
        for name in interviewers.split(',')
        if name.strip()
    ],
    'interview_rounds': int(interview_rounds) if interview_rounds else None,
    'technical_questions': [
        question.strip()
        for question in technical_questions.split(',')
        if question.strip()
    ],
    'rating': int(rating) if rating else None
}

    interview_data_json = json.dumps(interview_data)

    # job id name is required
    if not job_id:
        flash("job id is required.")
        return redirect(url_for('applications'))

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        # Insert the new application into MySQL
        query = """
            INSERT INTO applications
            (job_id, application_date, status, resume_version, cover_letter_sent,
            response_date, interview_date, notes, interview_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

        values = (
            job_id,
            application_date or None,
            status or None,
            resume_version or None,
            cover_letter_sent or None,
            response_date or None,
	    interview_date or None,
            notes or None,
            interview_data_json or None
        )

        cursor.execute(query, values)

        connection.commit()

        flash("application added successfully!")

    except Exception as error:
        connection.rollback()
        flash(f"Error adding application: {error}")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('applications')) 

# CREATE - Add a new job
@app.route('/jobs/add', methods=['POST'])
def add_jobs():

    # Get information submitted through the HTML form
    company_id = request.form.get('company_id', '').strip()
    job_title = request.form.get('job_title', '').strip()
    job_description = request.form.get('job_description', '').strip()
    salary_min = request.form.get('salary_min', '').strip()
    salary_max = request.form.get('salary_max', '').strip()
    job_type = request.form.get('job_type', '').strip()
    posting_url = request.form.get('posting_url', '').strip()
    date_posted = request.form.get('date_posted', '').strip()
    is_active = request.form.get('is_active', '0')

    # Get JSON requirements information
    required_skills = request.form.get('required_skills', '')
    preferred_skills = request.form.get('preferred_skills', '')
    education = request.form.get('education', '').strip()
    experience_years = request.form.get('experience_years', '').strip()
    remote_option = request.form.get('remote_option') == '1'

    # Convert skills into Python lists
    required_skills = [
        skill.strip()
        for skill in required_skills.split(',')
        if skill.strip()
    ]

    preferred_skills = [
        skill.strip()
        for skill in preferred_skills.split(',')
        if skill.strip()
    ]

    # Build the requirements JSON object
    requirements = {
        'required_skills': required_skills,
        'preferred_skills': preferred_skills,
        'education': education or None,
        'experience_years': int(experience_years) if experience_years else None,
        'remote_option': remote_option
    }

    # Convert the Python dictionary into JSON
    requirements_json = json.dumps(requirements)

    # Check required fields
    if not company_id or not job_title:
        flash("Company and job title are required.")
        return redirect(url_for('jobs'))

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        # Insert the new job into MySQL
        query = """
            INSERT INTO jobs
            (company_id, job_title, job_description, salary_min,
             salary_max, job_type, posting_url, date_posted,
             is_active, requirements)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            company_id,
            job_title,
            job_description or None,
            salary_min or None,
            salary_max or None,
            job_type or None,
            posting_url or None,
            date_posted or None,
            is_active,
            requirements_json
        )

        cursor.execute(query, values)
        connection.commit()

        flash("Job added successfully!")

    except Exception as error:
        connection.rollback()
        flash(f"Error adding job: {error}")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('jobs'))
# edit Comapanies 
@app.route('/companies/edit/<int:company_id>', methods=['POST'])
def edit_company(company_id):

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        # If the form was submitted, update the company
        if request.method == 'POST':
            company_name = request.form.get('company_name', '').strip()
            industry = request.form.get('industry', '').strip()
            website = request.form.get('website', '').strip()
            city = request.form.get('city', '').strip()
            state = request.form.get('state', '').strip()
            notes = request.form.get('notes', '').strip()

            if not company_name:
                flash("Company name is required.")
                return redirect(url_for('companies'))

            query = """
                UPDATE companies
                SET company_name = %s,
                    industry = %s,
                    website = %s,
                    city = %s,
                    state = %s,
                    notes = %s
                WHERE company_id = %s
            """

            values = (
                company_name,
                industry or None,
                website or None,
                city or None,
                state or None,
                notes or None,
                company_id
            )

            cursor.execute(query, values)
            connection.commit()

        return redirect(url_for('companies'))

    except Exception as error:
        connection.rollback()
        flash(f"Error updating company: {error}")
        return redirect(url_for('companies'))

    finally:
        cursor.close()
        connection.close()

# edit contacts
@app.route('/contacts/edit/<int:contact_id>', methods=['POST'])
def edit_contacts(contact_id):

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        # If the form was submitted, update the contact
        if request.method == 'POST':
            company_id = request.form.get('company_id', '').strip()
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            job_title = request.form.get('job_title', '').strip()
            linkedin_url = request.form.get('linkedin_url', '').strip()
            notes = request.form.get('notes', '').strip()

            if not company_id:
                flash("Company id is required.")
                return redirect(url_for('contacts'))

            query = """
                UPDATE contacts
                SET company_id = %s,
                    first_name = %s,
                    last_name = %s,
                    email = %s,
                    phone = %s,
		            job_title = %s,
		            linkedin_url = %s,
                    notes = %s
                WHERE contact_id = %s
            """

            values = (
                company_id,
                first_name or None,
                last_name or None,
                email or None,
                phone or None,
                job_title or None,
 		        linkedin_url or None,
 		        notes or None,
                contact_id
            )

            cursor.execute(query, values)
            connection.commit()

            flash("contact updated successfully!")
            return redirect(url_for('contacts'))

       

    except Exception as error:
        connection.rollback()
        flash(f"Error updating contact: {error}")
        return redirect(url_for('contacts'))

    finally:
        cursor.close()
        connection.close()

# edit applications
@app.route('/applications/edit/<int:application_id>', methods=['POST'])
def edit_applications(application_id):

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        # If the form was submitted, update the application
        if request.method == 'POST':
            job_id = request.form.get('job_id', '').strip()
            application_date = request.form.get('application_date', '').strip()
            status = request.form.get('status', '').strip()
            resume_version = request.form.get('resume_version', '').strip()
            cover_letter_sent = request.form.get('cover_letter_sent', '').strip()
            response_date = request.form.get('response_date', '').strip()
            interview_date = request.form.get('interview_date', '').strip()
            notes = request.form.get('notes', '').strip()
            # Get interview information
            feedback = request.form.get('feedback', '').strip()
            next_steps = request.form.get('next_steps', '').strip()
            interviewers = request.form.get('interviewers', '').strip()
            interview_rounds = request.form.get('interview_rounds', '').strip()
            technical_questions = request.form.get('technical_questions', '').strip()
            rating = request.form.get('rating', '').strip()

            # Build interview information JSON
            interview_data = {
                'feedback': feedback or None,
                'next_steps': next_steps or None,
                'interviewers': [
                    name.strip()
                    for name in interviewers.split(',')
                    if name.strip()
                ],
                'interview_rounds': int(interview_rounds) if interview_rounds else None,
                'technical_questions': [
                    question.strip()
                    for question in technical_questions.split(',')
                    if question.strip()
                ],
                'rating': int(rating) if rating else None
            }

            interview_data_json = json.dumps(interview_data)

            if not job_id:
                flash("job id is required.")
                return redirect(url_for('applications'))

            query = """
                UPDATE applications
                SET job_id = %s,
                    application_date = %s,
                    status = %s,
                    resume_version = %s,
                    cover_letter_sent = %s,
                    response_date = %s,
                    interview_date = %s,
                    notes = %s,
                    interview_data = %s
                WHERE application_id = %s
            """

            values = (
                job_id,
                application_date or None,
                status or None,
                resume_version or None,
                cover_letter_sent or None,
                response_date or None,
                interview_date or None,
                notes or None,
                interview_data_json,
                application_id
            )

            cursor.execute(query, values)
            connection.commit()

            flash("application updated successfully!")
            return redirect(url_for('applications'))

       

    except Exception as error:
        connection.rollback()
        flash(f"Error updating application: {error}")
        return redirect(url_for('applications'))

    finally:
        cursor.close()
        connection.close()

# UPDATE - Edit jobs
@app.route('/jobs/edit/<int:job_id>', methods=['POST'])
def edit_jobs(job_id):

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        # Get information submitted through the HTML form
        company_id = request.form.get('company_id', '').strip()
        job_title = request.form.get('job_title', '').strip()
        job_description = request.form.get('job_description', '').strip()
        salary_min = request.form.get('salary_min', '').strip()
        salary_max = request.form.get('salary_max', '').strip()
        job_type = request.form.get('job_type', '').strip()
        posting_url = request.form.get('posting_url', '').strip()
        date_posted = request.form.get('date_posted', '').strip()
        is_active = request.form.get('is_active', '0')

        # Get JSON requirements information
        required_skills = request.form.get('required_skills', '')
        preferred_skills = request.form.get('preferred_skills', '')
        education = request.form.get('education', '').strip()
        experience_years = request.form.get('experience_years', '').strip()
        remote_option = request.form.get('remote_option') == '1'

        # Convert skills into Python lists
        required_skills = [
            skill.strip()
            for skill in required_skills.split(',')
            if skill.strip()
        ]

        preferred_skills = [
            skill.strip()
            for skill in preferred_skills.split(',')
            if skill.strip()
        ]

        # Build the requirements JSON object
        requirements = {
            'required_skills': required_skills,
            'preferred_skills': preferred_skills,
            'education': education or None,
            'experience_years': int(experience_years) if experience_years else None,
            'remote_option': remote_option
        }

        requirements_json = json.dumps(requirements)

        # Check required fields
        if not company_id or not job_title:
            flash("Company and job title are required.")
            return redirect(url_for('jobs'))

        query = """
            UPDATE jobs
            SET company_id = %s,
                job_title = %s,
                job_description = %s,
                salary_min = %s,
                salary_max = %s,
                job_type = %s,
                posting_url = %s,
                date_posted = %s,
                is_active = %s,
                requirements = %s
            WHERE job_id = %s
        """

        values = (
            company_id,
            job_title,
            job_description or None,
            salary_min or None,
            salary_max or None,
            job_type or None,
            posting_url or None,
            date_posted or None,
            is_active,
            requirements_json,
            job_id
        )

        cursor.execute(query, values)
        connection.commit()

        flash("Job updated successfully!")
        return redirect(url_for('jobs'))

    except Exception as error:
        connection.rollback()
        flash(f"Error updating job: {error}")
        return redirect(url_for('jobs'))

    finally:
        cursor.close()
        connection.close()

#delete companies
@app.route('/companies/delete/<int:company_id>', methods=['POST'])

def delete_company(company_id):

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        query = """
            DELETE FROM companies
            WHERE company_id = %s
        """

        cursor.execute(query, (company_id,))
        connection.commit()

        if cursor.rowcount > 0:
            flash("Company deleted successfully!")
        else:
            flash("Company not found.")

    except Exception as error:
        connection.rollback()
        flash(f"Error deleting company: {error}")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('companies'))

#delete contacts
@app.route('/contacts/delete/<int:contact_id>', methods=['POST'])

def delete_contacts(contact_id):

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        query = """
            DELETE FROM contacts
            WHERE contact_id = %s
        """

        cursor.execute(query, (contact_id,))
        connection.commit()

        if cursor.rowcount > 0:
            flash("Contact deleted successfully!")
        else:
            flash("Contact not found.")

    except Exception as error:
        connection.rollback()
        flash(f"Error deleting contact: {error}")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('contacts'))

#delete applications
@app.route('/applications/delete/<int:application_id>', methods=['POST'])

def delete_application(application_id):

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        query = """
            DELETE FROM applications
            WHERE application_id = %s
        """

        cursor.execute(query, (application_id,))
        connection.commit()

        if cursor.rowcount > 0:
            flash("application deleted successfully!")
        else:
            flash("application not found.")

    except Exception as error:
        connection.rollback()
        flash(f"Error deleting application: {error}")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('applications'))

#delete jobs
@app.route('/jobs/delete/<int:job_id>', methods=['POST'])

def delete_job(job_id):

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        query = """
            DELETE FROM jobs
            WHERE job_id = %s
        """

        cursor.execute(query, (job_id,))
        connection.commit()

        if cursor.rowcount > 0:
            flash("job deleted successfully!")
        else:
            flash("job not found.")

    except Exception as error:
        connection.rollback()
        flash(f"Error deleting job: {error}")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('jobs'))

if __name__ == '__main__':
    app.run(debug=True)