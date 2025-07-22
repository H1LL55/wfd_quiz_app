from flask import Blueprint, redirect, render_template, request, session, url_for
from quiz_app.routes.db_connection_bp import get_db_connection


user_dash_bp = Blueprint('user_dash_bp', __name__)


@user_dash_bp.route('/dashboard')
def user_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    if conn is None:
        return "Database connection failed."
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT score, total, percentage, message, timestamp FROM quiz_results"
            " WHERE user_email = %s ORDER BY timestamp DESC",
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
