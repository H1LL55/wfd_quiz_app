from flask import Blueprint, redirect, render_template, request, session, url_for
from quiz_app.routes.db_connection_bp import get_db_connection
from quiz_app.routes.quiz_settings_bp import get_random_questions

employee_dash_bp = Blueprint('employee_dash_bp', __name__)

@employee_dash_bp.route('/view_dash/<username>')
def view_admin_dash(username):

    if "user" not in session:
        return redirect(url_for("login_bp.login"))
    
    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, email FROM users WHERE email = %s", (username,))

    user = cursor.fetchone()

    if not user:
        return "User not found"

    #get quiz results
    cursor.execute("SELECT score, total, percentage, message, timestamp FROM quiz_results WHERE user_email = %s", (username,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("employee_dash.html", user=user, results=results)
    

