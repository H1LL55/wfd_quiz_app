from flask import Flask, request, render_template, redirect, url_for, session
from flask_bcrypt import Bcrypt
import os
from dotenv import load_dotenv

#blueprints
from quiz_app.routes.quiz_bp import quiz_bp
from quiz_app.routes.login_bp import login_bp
from quiz_app.routes.employee_dash_bp import employee_dash_bp
from quiz_app.routes.admin_dash_bp import admin_dash_bp
from quiz_app.routes.db_connection_bp import db_connection_bp
from quiz_app.routes.db_connection_bp import get_db_connection
from quiz_app.routes.quiz_settings_bp import quiz_settings_bp
from quiz_app.routes.user_dash_bp import user_dash_bp
from quiz_app.routes.add_question_bp import add_question_bp
from quiz_app.routes.quiz_settings_bp import get_random_questions

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret_key")
bcrypt = Bcrypt(app)

app.register_blueprint(quiz_bp)

app.register_blueprint(login_bp)

app.register_blueprint(employee_dash_bp)

app.register_blueprint(admin_dash_bp)

app.register_blueprint(db_connection_bp)

app.register_blueprint(quiz_settings_bp)

app.register_blueprint(user_dash_bp)

app.register_blueprint(add_question_bp)

from waitress import serve

if __name__ == "__main__":
    app.run(debug=True)