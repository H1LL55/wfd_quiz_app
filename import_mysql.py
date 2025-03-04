from flask import Flask, request, render_template, redirect, url_for, session
import psycopg2
import psycopg2.extras
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a secure key later
bcrypt = Bcrypt(app)

# Database connection function
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            user="postgres",
            password="Blacksabbath3412!",  # Replace later with os.getenv("DB_PASSWORD")
            database="testing_python"
        )
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        return None

# Home route (Registration page)
@app.route('/')
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template('test.html')

# Registration submission route
@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    conn = get_db_connection()
    if conn is None:
        return "Database connection failed."

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO testing (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        conn.commit()
        print("User added to database")
    except psycopg2.IntegrityError:
        print("User already exists")
        return "Email already registered. <a href='/login'>Login here</a>"
    finally:
        cursor.close()
        conn.close()

    return "Registration successful! <a href='/login'>Login here</a>"

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        if conn is None:
            return "Database connection failed."

        cursor = conn.cursor()
        cursor.execute('SELECT password FROM testing WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user[0], password):
            session["user"] = email
            return redirect(url_for("dashboard"))
        else:
            return "Invalid email or password."

        cursor.close()
        conn.close()

    return render_template('login.html')

# Dashboard route (Protected)
@app.route('/home')
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("homepage.html", user=session["user"])

# Logout route
@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# Fetch random questions from quiz_questions
def get_random_questions(limit=10):
    conn = get_db_connection()
    if conn is None:
        return []

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(f"SELECT * FROM quiz_questions ORDER BY RANDOM() LIMIT {limit}")
    questions = cursor.fetchall()
    cursor.close()
    conn.close()
    return questions

# Quiz route
@app.route('/quiz')
def quiz():
    if "user" not in session:
        return redirect(url_for("login"))

    questions = get_random_questions()
    return render_template("quiz.html", questions=questions)

# Submit quiz answers
@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if "user" not in session:
        return redirect(url_for("login"))

    user_answers = request.form
    score = 0

    conn = get_db_connection()
    if conn is None:
        return "Database connection failed."

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    for question_id, user_answer in user_answers.items():
        cursor.execute("SELECT correct_option FROM quiz_questions WHERE id = %s", (question_id,))
        result = cursor.fetchone()
        if result and user_answer == result["correct_option"]:
            score += 1

    cursor.close()
    conn.close()

    return render_template("quiz_result.html", score=score, total=len(user_answers))

# Add question route (restricted to specific users)
@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if "user" not in session:
        return redirect(url_for("login"))

    allowed_users = ["georgie.warlosz@wood-finishes-direct.com", "jenna.hills@wood-finishes-direct.com"]
    if session["user"] not in allowed_users:
        return "Access Denied: You are not authorized to add questions."

    if request.method == 'POST':
        question = request.form['question']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_option = request.form['correct_option'].upper()
        category = request.form['category']
        level = request.form['level']
        product = request.form.get('product', None)  # Optional field

        if correct_option not in ['A', 'B', 'C', 'D']:
            return "Invalid correct option. Please enter A, B, C, or D."

        conn = get_db_connection()
        if conn is None:
            return "Database connection failed."

        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO quiz_questions (question, option_a, option_b, option_c, option_d, correct_option, category, level, product) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (question, option_a, option_b, option_c, option_d, correct_option, category, level, product)
            )
            conn.commit()
        except psycopg2.Error as e:
            return f"Error adding question: {e}"
        finally:
            cursor.close()
            conn.close()

        return "Question added successfully! <a href='/add_question'>Add another</a> | <a href='/home'>Go Home</a>"

    return render_template("add_question.html")

from waitress import serve


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)