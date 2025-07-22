import bcrypt
from flask import Blueprint, app, redirect, render_template, request, session, url_for
import mysql.connector
from flask_bcrypt import Bcrypt


bcrypt = Bcrypt()

login_bp = Blueprint('login_bp', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host="testing-clone-cluster.cluster-cfejsghstklo.eu-west-1.rds.amazonaws.com",
        user="quiz_app",
        password="IG2wa[3Prfij-MzT",
        database="quiz_app"
    )
@login_bp.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    hashed_password = Bcrypt.generate_password_hash(password).decode('utf-8')
    conn = get_db_connection()
    if conn is None:
        return "Database connection failed."
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        conn.commit()
        print("User added to database")
    except Exception as e:
        print("User already exists or error:", e)
        return "Email already registered. <a href='/login'>Login here</a>"
    finally:
        cursor.close()
        conn.close()
    return "Registration successful! <a href='/login'>Login here</a>"

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = get_db_connection()
        if conn is None:
            return "Database connection failed."
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and bcrypt.check_password_hash(user[0], password):
            session["user"] = email
            return redirect(url_for("login_bp.dashboard"))
        else:
            return "Invalid email or password."
    return render_template('login.html')

@login_bp.route('/home')
def dashboard():
    if "user" not in session:
        return redirect(url_for("login_bp.login"))
    return render_template("homepage.html", user=session["user"])

@login_bp.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("login_bp.login"))
