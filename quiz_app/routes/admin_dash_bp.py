from flask import Blueprint, redirect, render_template, request, session, url_for
from quiz_app.routes.db_connection_bp import get_db_connection

admin_dash_bp = Blueprint('admin_dash_bp', __name__)

@admin_dash_bp.route('/admin_dash')
def admin_dashboard():
    # access list for users 
    allowed_admins = [
        "antony.burford@wood-finishes-direct.com",
        "jenna.hills@wood-finishes-direct.com",
        "jennahillss@gmail.com" 
    ] 
    if "user" not in session or session["user"].strip().lower() not in [u.lower() for u in allowed_admins]:
        return "access denied"
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT email, name FROM users")
    users = cursor.fetchall()
    
    employees = [{"username": user["email"], "name": user["name"]} for user in users]

    cursor.close()
    conn.close()

    return render_template("admin_dash.html", employees=employees)
