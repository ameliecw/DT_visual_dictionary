from flask import Flask, render_template, redirect, request
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from flask import session

app = Flask(__name__)
DATABASE = "database.db"
bcrypt = Bcrypt(app)
app.secret_key = "ueuywq9571"


def create_connection(db_file):
  """create connection to the database"""
  try:
    connection = sqlite3.connect(db_file)
    return connection
  except Error as e:
    print(e)
  return None


#home page function
@app.route('/')
def render_homepage():
  return render_template('home.html')


#login function
@app.route('/login', methods=['POST', 'GET'])
def render_login_page():
  return render_template('login.html')


#about function
@app.route('/about')
def render_contact_page():
  return render_template('about.html')


if __name__ == "__main__":
  app.run(host='0.0.0.0', port=81)
