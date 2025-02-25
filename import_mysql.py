from flask import Flask, request, render_template, redirect, url_for, session
import mysql.connector
from flask_bcrypt import Bcrypt
import os  # Added for environment variable handling

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")  # Use env var for security
bcrypt = Bcrypt(app)

# Database configuration (use environment variables for deployment)
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "Blacksabbath3412!"),
        database=os.getenv("DB_NAME", "testing_python")
    )

# HTML form route for Registering Page
@app.route('/')
def home():
    if "user" in session:  # Check if user is logged in
        return redirect(url_for("dashboard"))
    return render_template('test.html')

# Form submission route (Register User)
@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Connect to MySQL
    db = get_db_connection()
    cursor = db.cursor()

    # Insert form data into MySQL
    try:
        cursor.execute("INSERT INTO testing (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))
        db.commit()
        print("User added to database")
    except mysql.connector.IntegrityError:
        print("User already exists")
    finally:
        db.close()

    return "Registration successful! <a href='/login'>Login here</a>"

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Connect to MySQL
        db = get_db_connection()
        cursor = db.cursor()

        # Fetch user password from the database
        query = 'SELECT password FROM testing WHERE email = %s'
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if user:
            stored_hashed_password = user[0]  # Get hashed password
            if bcrypt.check_password_hash(stored_hashed_password, password):
                session["user"] = email  # Store user in session
                db.close()
                return redirect(url_for("dashboard"))
            else:
                db.close()
                return "Invalid email or password."
        else:
            db.close()
            return "User not found."

    return render_template('login.html')

# Home Dashboard Route (Protected)
@app.route('/home')
def dashboard():
    if "user" in session:  # Check if user is logged in
        return render_template("homepage.html", user=session["user"])
    return redirect(url_for("login"))

# Logout Route
@app.route('/logout')
def logout():
    session.pop("user", None)  # Remove user session
    return redirect(url_for("login"))

# Function to get random questions from the database
def get_random_questions(limit=10):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)  # dictionary=True returns results as dictionaries

    # Fetch random questions
    cursor.execute(f"SELECT * FROM quiz_questions ORDER BY RAND() LIMIT {limit}")
    questions = cursor.fetchall()

    db.close()
    return questions

# Route to display the quiz
@app.route('/quiz')
def quiz():
    if "user" not in session:
        return redirect(url_for("login"))

    questions = get_random_questions()
    return render_template("quiz.html", questions=questions)

# Route to process quiz answers
@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if "user" not in session:
        return redirect(url_for("login"))

    user_answers = request.form  # Get submitted answers
    score = 0

    # Connect to DB to check answers
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    for question_id, user_answer in user_answers.items():
        cursor.execute("SELECT correct_option FROM quiz_questions WHERE id = %s", (question_id,))
        correct_option = cursor.fetchone()["correct_option"]

        if user_answer == correct_option:
            score += 1  # Increment score for correct answers

    db.close()

    return f"Quiz complete! Your score: {score}/{len(user_answers)}"

@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if "user" not in session:  # Ensure the user is logged in
        return redirect(url_for("login"))

    # Restrict access to only Georgie and Jenna
    if session["user"] not in ["georgie.warlosz@wood-finishes-direct.com", "jenna.hills@wood-finishes-direct.com"]:
        return "Access Denied: You are not authorized to add questions."

    if request.method == 'POST':  # When form is submitted
        question = request.form['question']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_option = request.form['correct_option'].upper()  # Ensure it's uppercase (A, B, C, or D)
        category = request.form['category']
        level = request.form['level']

        # Validate correct option
        if correct_option not in ['A', 'B', 'C', 'D']:
            return "Invalid correct option. Please enter A, B, C, or D."

        # Connect to database
        db = get_db_connection()
        cursor = db.cursor()

        # Insert into DB
        cursor.execute(
            "INSERT INTO quiz_questions (question, option_a, option_b, option_c, option_d, correct_option, category, level) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (question, option_a, option_b, option_c, option_d, correct_option, category, level)
        )
        db.commit()
        db.close()

        return "Question added successfully! <a href='/add_question'>Add another</a> | <a href='/home'>Go Home</a>"

    return render_template("add_question.html")  # Show the form if GET request

# Remove the if __name__ == "__main__" block for Gunicorn compatibility
# Gunicorn will directly use the 'app' object as the WSGI callable