from flask import Flask, request, render_template, redirect, url_for, session
import psycopg2
import psycopg2.extras
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret_key")
bcrypt = Bcrypt(app)

def get_db_connection():
    try:
        DATABASE_URL = os.environ.get("DATABASE_URL")
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL is not set.")
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

@app.route('/')
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template('test.html')

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

@app.route('/home')
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("homepage.html", user=session["user"])

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

def get_random_questions(limit=10):
    conn = get_db_connection()
    if conn is None:
        print("No database connection for questions")
        return []
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cursor.execute(f"SELECT * FROM quiz_questions ORDER BY RANDOM() LIMIT {limit}")
        questions = cursor.fetchall()
        print(f"Fetched {len(questions)} questions")
        return questions
    except Exception as e:
        print(f"Query error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

@app.route('/quiz')
def quiz():
    if "user" not in session:
        return redirect(url_for("login"))
    questions = get_random_questions()
    print(f"Rendering quiz with {len(questions)} questions")
    return render_template("quiz.html", questions=questions)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if "user" not in session:
        return redirect(url_for("login"))
    user_answers = request.form
    print(f"Received answers: {dict(user_answers)}")
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
    total = len(user_answers)
    message = "Well done!" if score / total >= 0.7 else "Better luck next time!"
    print(f"Quiz result: score={score}, total={total}, message={message}")
    return render_template("quiz_result.html", score=score, total=total, message=message)
    percentage = (score / total) * 100

    try:
        cursor.execute(
            "INSERT INTO quiz_results (user_email, score, total, percentage, message) VALUES (%s, %s, %s, %s, %s)",
            (session["user"], score, total, percentage, message)
        )
        conn.commit()
    except Exception as e:
        print(f"Failed to save quiz result: {e}")

@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if "user" not in session:
        return redirect(url_for("login"))
    allowed_users = ["georgie.warlosz@wood-finishes-direct.com", "jenna.hills@wood-finishes-direct.com", "antony.burford@wood-finishes-direct.com", "jennahillss@gmail.com"]
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
        product = request.form.get('product', None)
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
            print("Question added successfully")
        except psycopg2.Error as e:
            return f"Error adding question: {e}"
        finally:
            cursor.close()
            conn.close()
        return "Question added successfully! <a href='/add_question'>Add another</a> | <a href='/home'>Go Home</a>"
    return render_template("add_question.html")
# Quiz route
@app.route('/quiz')
def quiz():
    if "user" not in session:
        return redirect(url_for("login"))

    questions = get_random_questions()
    return render_template("quiz.html", questions=questions)

# Submit all quiz answers
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

    total = len(user_answers)
    if score > 8: #this can be adjusted when the quizzes are made larger, needs to be 70% or above 
        message = "Well done!"
    else:
        message = "Better luck next time!"

    return render_template("quiz_result.html", score=score, total=total, message=message)
    
# add thes question route (restricted to specific users)
@app.route('/dashboard')
def user_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    if conn is None:
        return "Database connection failed."
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        cursor.execute(
            "SELECT score, total, percentage, message, timestamp FROM quiz_results WHERE user_email = %s ORDER BY timestamp DESC",
            (session["user"],)
        )
        results = cursor.fetchall()
    except Exception as e:
        print(f"Failed to fetch results: {e}")
        results = []
    finally:
        cursor.close()
        conn.close()

    return render_template("dashboard.html", results=results, user=session["user"])

from waitress import serve


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  
    app.run(host="0.0.0.0", port=port, debug=True)