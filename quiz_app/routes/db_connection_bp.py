import mysql.connector
from flask import Blueprint, redirect, render_template, request, session, url_for   
from flask_bcrypt import Bcrypt 

db_connection_bp = Blueprint('db_connection_bp',__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="testing-clone-cluster.cluster-cfejsghstklo.eu-west-1.rds.amazonaws.com",
        user="quiz_app",
        password="IG2wa[3Prfij-MzT",
        database="quiz_app"
    )