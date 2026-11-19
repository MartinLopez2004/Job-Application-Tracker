# Job Application Tracker

## Project Description

The Job Application Tracker is a full-stack web application designed to help users organize and manage their job search.

The application allows users to manage companies, job listings, job applications, and professional contacts. It also includes a dashboard for viewing statistics and a Job Match feature that compares user skills with job requirements.

## Technologies Used

- Python
- Flask
- MySQL
- HTML
- CSS
- JavaScript
- GenAI assistance (ChatGPT)

## Features

- Dashboard with application statistics
- Companies management (Create, Read, Update, Delete)
- Jobs management (Create, Read, Update, Delete)
- Applications management (Create, Read, Update, Delete)
- Contacts management (Create, Read, Update, Delete)
- JSON data storage for job requirements and interview information
- Job Match feature that ranks jobs by skill match percentage

## Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_LINK
cd dbproject
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up the Database

- Open MySQL Workbench.
- Run the `schema.sql` script to create the database and tables.
- Make sure your MySQL server is running.

### 4. Configure Environment Variables

Create a `.env` file in the project folder and configure the database connection settings required by `db_connection.py`.

Do not upload your database password or secret key to GitHub.

### 5. Run the Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000/
```

## Project Structure

```text
dbproject/
├── app.py
├── db_connection.py
├── schema.sql
├── templates/
├── static/
├── README.md
├── AI_USAGE.md
└── requirements.txt
```

## Database

The application uses MySQL with four main tables:

- companies
- jobs
- applications
- contacts

The database includes foreign-key relationships and JSON columns for job requirements and interview information.