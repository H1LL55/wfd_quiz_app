

from flask import Blueprint, redirect, render_template, request, session, url_for
import mysql.connector
from flask_bcrypt import Bcrypt
from quiz_app.routes.db_connection_bp import db_connection_bp
from quiz_app.routes.db_connection_bp import get_db_connection
from quiz_app.routes.quiz_settings_bp import get_random_questions

quiz_bp = Blueprint('quiz_bp', __name__)


@quiz_bp.route('/quiz', methods=['GET', 'POST'])
def quiz():
    from wfdquiz import get_random_questions 
    
    if "user" not in session:
        return redirect(url_for("login"))
    
    if 'quiz_progress' not in session:
        session['quiz_progress'] = {
            'current': 0,
            'answers': {},
            'questions': get_random_questions()
        }

    progress = session['quiz_progress']
    questions = progress['questions']

    if request.method == 'POST':
        prev_q = questions[progress['current']]['id']
        answer = request.form.get('answer')
        progress['answers'][str(prev_q)] = answer
        progress['current'] += 1
        session['quiz_progress'] = progress

    if progress['current'] >= len(questions):
        session['quiz_answers'] = progress['answers']  
        session.pop('quiz_progress')
        return redirect(url_for('quiz_bp.submit_quiz'))

    current_q = questions[progress['current']]
    return render_template("quiz.html", question=current_q, index=progress['current'] + 1, total=len(questions))

@quiz_bp.route('/submit_quiz', methods=['GET', 'POST'])
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
