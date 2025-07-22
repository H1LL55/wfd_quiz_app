from flask import Blueprint, redirect, render_template, request, session, url_for
from quiz_app.routes.db_connection_bp import get_db_connection


quiz_settings_bp = Blueprint('quiz_settings_bp',__name__)

ADMIN_EMAILS = [ 
    'jenna.hills@wood-finishes-direct.com',
    'georgie.warlosz@wood-finishes-direct.com',
    'antony.burford@wood-finishes-direct.com',
]

#standard 10 question quiz
@quiz_settings_bp.route('/')
def home():
    if "user" in session:
        return redirect(url_for("login_bp.dashboard"))
    return render_template('test.html')

def get_random_questions(limit=10):
    conn = get_db_connection()
    if conn is None:
        print("No database connection for questions")
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT * FROM aanswers1 ORDER BY RAND() LIMIT %s", (limit,))
        questions = cursor.fetchall()
        print(f"Fetched {len(questions)} questions")
        return questions
    except Exception as e:
        print(f"Query error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

@quiz_settings_bp.route('/employee_quiz_settings')
def employee_quiz_settings():
    if "user" not in session or session["user"] not in ADMIN_EMAILS:
        return "Unauthorized", 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT DISTINCT level FROM aanswers1")
        levels = [row['level'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT category FROM aanswers1")
        categories = [row['category'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT product FROM aanswers1 WHERE product IS NOT NULL AND product != ''")
        products = [row['product'] for row in cursor.fetchall()]

        # hardcoded list of employee emails for now (or fetch from db if you have a user table)
        employee_emails = [
            "jenna.hills@wood-finishes-direct.com",
            "georgie.warlosz@wood-finishes-direct.com",
            "antony.burford@wood-finishes-direct.com",
            "new.employee@example.com"
        ]

    except Exception as e:
        print(f"Error fetching quiz settings data: {e}")
        levels, categories, products, employee_emails = [], [], [], []
    finally:
        cursor.close()
        conn.close()

    return render_template(
        'employee_quiz_settings.html',
        levels=levels,
        categories=categories,
        products=products,
        employee_emails=employee_emails
    )

@quiz_settings_bp.route('/quiz_by_filter', methods=['POST'])
def quiz_by_filter():
    filter_type = request.form.get('filter_type')
    filter_value = request.form.get('filter_value')
    amount = int(request.form.get('amount', 10))  # default to 10 if missing

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try: 
        query = f"SELECT * FROM aanswers1 WHERE {filter_type} = %s ORDER BY RAND() LIMIT %s"
        cursor.execute(query, (filter_value, amount))
        questions = cursor.fetchall()
    except Exception as e:
        print(f"Error filtering quiz: {e}")
        questions = []
    finally:
        cursor.close()
        conn.close()

    return render_template("quiz_page.html", questions=questions)

@quiz_settings_bp.route('/save_quiz_settings', methods=['POST'])
def save_quiz_settings():
    if "user" not in session or session["user"] not in ADMIN_EMAILS:
        return "Unauthorized", 403

    email = request.form.get("email")
    level = request.form.get("level")
    category = request.form.get("category")
    product = request.form.get("product")
    question_count = request.form.get("question_count")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO quiz_settings (email, level, category, product, question_count)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                level = VALUES(level),
                category = VALUES(category),
                product = VALUES(product),
                question_count = VALUES(question_count)
        """, (email, level, category, product, question_count))
        conn.commit()
    except Exception as e:
        print(f"Failed to save quiz settings: {e}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('quiz_settings_bp.employee_quiz_settings'))


@quiz_settings_bp.route('/agent_quiz', methods=['GET', 'POST'])
def agent_quiz():
    if "user" not in session:
        return redirect(url_for("login_bp.login"))

    email = session["user"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    try:
        #if no quiz session shuffle based on filter
        if 'agent_quiz_questions' not in session:
            cursor.execute("SELECT * FROM quiz_settings WHERE email = %s", (email,))
            settings = cursor.fetchone()

            if not settings:
                return "No quiz settings configured for this user", 400

            query = "SELECT * FROM aanswers1 WHERE 1=1"
            params = []

            if settings['level']:
                query += " AND level = %s"
                params.append(settings['level'])
            if settings['category']:
                query += " AND category = %s"
                params.append(settings['category'])
            if settings['product']:
                query += " AND product = %s"
                params.append(settings['product'])

            query += " ORDER BY RAND() LIMIT %s"
            params.append(settings['question_count'] or 10)

            cursor.execute(query, tuple(params))
            session['agent_quiz_questions'] = cursor.fetchall()
            session['agent_quiz_index'] = 0
            session['agent_quiz_score'] = 0

        questions = session['agent_quiz_questions']
        index = session['agent_quiz_index']

        # Handle submitted answer
        if request.method == 'POST':
            selected = request.form.get('answer')
            if selected and selected == questions[index]['correct_option']:
                session['agent_quiz_score'] += 1
            session['agent_quiz_index'] += 1
            index += 1

        # Show next question or finish
        if index >= len(questions):
            score = session['agent_quiz_score']
            session.pop('agent_quiz_questions', None)
            session.pop('agent_quiz_index', None)
            session.pop('agent_quiz_score', None)
            return f"Quiz complete! You scored {score} out of {len(questions)}"

        return render_template(
            "quiz_page.html",
            question=questions[index],
            index=index + 1,
            total=len(questions)
        )

    except Exception as e:
        print(f"Agent quiz error: {e}")
        return "Something went wrong loading the quiz", 500
    finally:
        cursor.close()
        conn.close()

@quiz_settings_bp.route('/submit_quiz', methods=['GET', 'POST'])
def submit_quiz():
    if "user" not in session:
        return redirect(url_for("login"))

    user_answers = session.get('quiz_answers', {})
    print(f"Received answers: {dict(user_answers)}")
    score = 0
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed."
    cursor = conn.cursor(dictionary=True)

    # Calculate score
    for question_id, user_answer in user_answers.items():
        cursor.execute("SELECT correct_option FROM aanswers1 WHERE id = %s", (question_id,))
        result = cursor.fetchone()

        print(f"QID: {question_id}, User: {user_answer}, Correct: {result['correct_option']}")

        if result:
            correct = result["correct_option"]

            if user_answer.strip().upper() == correct.strip().upper():
                score += 1
    
    total = len(user_answers)
    percentage = (score / total) * 100 if total > 0 else 0
    message = "Well done!" if percentage >= 70 else "Better luck next time!"

    
    try:
        cursor.execute(
            "INSERT INTO quiz_results (user_email, score, total, percentage, message) VALUES (%s, %s, %s, %s, %s)",
            (session["user"], score, total, percentage, message)
        )
        conn.commit()
        print("Quiz result saved successfully")
    except Exception as e:
        print(f"Failed to save quiz result: {e}")
    finally:
        cursor.close()
        conn.close()

    return render_template("quiz_result.html", score=score, total=total, message=message)

