from flask import Blueprint, redirect, render_template, request, session, url_for
from quiz_app.routes.db_connection_bp import db_connection_bp
from quiz_app.routes.db_connection_bp import get_db_connection


add_question_bp = Blueprint('add_question_bp', __name__)

@add_question_bp.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if "user" not in session:
        return redirect(url_for("login"))
    allowed_users = [
        "georgie.warlosz@wood-finishes-direct.com",
        "jenna.hills@wood-finishes-direct.com",
        "antony.burford@wood-finishes-direct.com",
        "jennahillss@gmail.com"
    ]
    if session["user"].strip().lower() not in [u.lower() for u in allowed_users]:
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
                "INSERT INTO aanswers1 (question, option_a, option_b, option_c, option_d, correct_option, category, level, product)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (question, option_a, option_b, option_c, option_d, correct_option, category, level, product)
            )
            conn.commit()
            print("Question added successfully")
        finally:
            cursor.close()
            conn.close()
        return "Question added successfully! <a href='/add_question'>Add another</a> | <a href='/home'>Go Home</a>"

    return render_template("add_question.html")