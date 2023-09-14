from flask import Flask, redirect, render_template, request
import sqlite3
import os.path
from sqlite3 import Error
from flask_bcrypt import Bcrypt, generate_password_hash
from flask import session

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "ueuywq9571"
DATABASE = "database.db"


#connect to the database
def create_connection(db_file):
  """create connection to the database"""
  try:
    connection = sqlite3.connect(db_file)
    return connection
  except Error as e:
    print(e)
  return None


def get_list(query, params):
  con = create_connection(DATABASE)
  cur = con.cursor()
  if params == "":
    cur.execute(query)
  else:
    cur.execute(query, params)
  query_list = cur.fetchall()
  con.close()
  return query_list


#user logged in or not
def is_logged_in():
  print(session.get("email"))
  print(session)
  if session.get("email") is None:
    print("Not logged in")
    return False
  else:
    print("Logged in")
    return True


#user is teacher or not
def is_teacher():
  if session.get("teacher") == 1:
    print("User is a teacher")
    return True
  else:
    print("User is not a teacher")
    return False


#home page function
@app.route('/')
def render_homepage():
  #select the current time and print from database
  #con = create_connection(DATABASE)
  #cur = con.cursor()
  #update = "INSERT INTO date_added(d1) VALUES(julianday('now'))"
  #cur.execute(update)
  #query = "SELECT date(d1), time(d1) FROM datetime_real"
  #cur.execute(query)
  #date = cur.fetchall()
  #print(date)
  #cur.execute(query)
  #con.close()

  message = request.args.get("message")
  print(message)
  if message is None:
    message = ""

  return render_template('home.html',
                         logged_in=is_logged_in(),
                         is_teacher=is_teacher(),
                         message=message)


#words page
@app.route('/words/<category_id>')
def render_words_page(category_id):
  #fetch categories
  category_list = get_list("SELECT * FROM categories", "")
  print(category_list)

  #fetch the words
  word_list = get_list(
      "SELECT * FROM words WHERE category_id = ? ORDER BY word_id",
      [category_id])
  print(word_list)

  con = create_connection(DATABASE)
  #get categories
  query = "SELECT * FROM categories"
  cur = con.cursor()
  cur.execute(query)
  category_list = cur.fetchall()
  print(category_list)
  n = 1
  for word in word_list:
    image = "image"

    query = "UPDATE words SET alt_text = image WHERE word_id = ?"
    cur = con.cursor()
    cur.execute(query, (n, ))
    n = n + 1
    list = cur.fetchall()
    print(list)

  #get words
  cur = con.cursor()
  query = "SELECT * FROM words WHERE category_id = ? ORDER BY word_id"
  cur.execute(query, (category_id, ))
  word_list = cur.fetchall()
  con.close()

  #return to main words page if no words found
  if not word_list:
    return redirect("/words?message=Word+was+not+found")

  print(word_list)
  message = request.args.get('message')
  print(message)
  if message is None:
    message = ""

  return render_template('words.html',
                         categories=category_list,
                         words=word_list,
                         logged_in=is_logged_in(),
                         is_teacher=is_teacher(),
                         message=message)


#search through words
@app.route('/words', methods=['POST'])
def search():
  category_list = get_list("SELECT * FROM categories", "")
  if request.method == "POST":
    print(request.form)
    search = request.form.get('search').lower().strip()
    print("Searched for:", search)

    con = create_connection(DATABASE)
    query = "SELECT * FROM words WHERE english_word LIKE ? OR maori_word LIKE ? OR description LIKE ? ORDER BY english_word"
    cur = con.cursor()
    cur.execute(query, (
        '%' + search + '%',
        '%' + search + '%',
        '%' + search + '%',
    ))
    result = cur.fetchall()  #only one value
    print(result)
    con.close()

  message = request.args.get('message')
  print(message)
  if message is None:
    message = ""

  return render_template('words.html',
                         logged_in=is_logged_in(),
                         is_teacher=is_teacher(),
                         words=result,
                         categories=category_list,
                         message=message)


#login function
@app.route('/login', methods=['POST', 'GET'])
def render_login_page():
  if is_logged_in():
    return redirect('/')

  if request.method == 'POST':
    email = request.form['email'].strip().lower()
    password = request.form['password'].strip()

    # Debug print statements
    print("Logging in")
    print("Input email:", email)
    print("Input password:", password)

    con = create_connection(DATABASE)
    if con is None:
      print("Failed to connect to the database")

    #cur = con.cursor()
    #new_hashed_password = generate_password_hash(password)
    #cur.execute("UPDATE user SET password = ? WHERE email = ?",
    #           (new_hashed_password, email))
    #con.commit()
    #con.close()

    con = create_connection(DATABASE)
    query = "SELECT user_id, fname, password, teacher FROM user WHERE email = ?"
    cur = con.cursor()
    cur.execute(query, (email, ))
    user_data = cur.fetchall()  #only one value
    con.close()
    print("User data:", user_data)

    if len(user_data) == 0:
      return redirect("/login?message=Email+invalid+or+password+incorrect")

    try:
      user_id = user_data[0][0]
      print(user_id)
      first_name = user_data[0][1]
      print(first_name)
      db_password = user_data[0][2]
      print(db_password)
      teacher = user_data[0][3]
      print(teacher)
    except IndexError:
      return redirect("/login?message=Email+invalid+or+password+incorrect")

    if not bcrypt.check_password_hash(db_password, password):
      return redirect("/login?message=Email+invalid+or+password+incorrect")

    session['email'] = email
    session['user_id'] = user_id
    session['firstname'] = first_name
    session['teacher'] = teacher

    # Debug print statement
    print("Login successful. Session:", session)
    return redirect("/?message=Successfully+logged+in")

  message = request.args.get('message')
  print(message)
  if message is None:
    message = ""

  return render_template('login.html',
                         logged_in=is_logged_in(),
                         is_teacher=is_teacher(),
                         message=message)


#logout function
@app.route('/logout')
def logout():
  print(list(session.keys()))
  [session.pop(key) for key in list(session.keys())]
  print(list(session.keys()))
  return redirect('/login?message=Logged+out+securely')

  message = request.args.get('message')
  print(message)
  if message is None:
    message = ""
  return render_template('home.html',
                         logged_in=is_logged_in(),
                         is_teacher=is_teacher(),
                         message=message)


#signup function
@app.route('/signup', methods=['POST', 'GET'])
def render_signup_page():
  if is_logged_in():
    return redirect('/menu/1')
  if request.method == 'POST':
    print(request.form)
    fname = request.form.get('fname').title().strip()
    lname = request.form.get('lname').title().strip()
    email = request.form.get('email').lower().strip()
    teacher = request.form.get('teacher')
    password = request.form.get('password')
    password2 = request.form.get('password2')

    print("TEacher from the form", teacher)

    if password != password2:
      print("Passwords do not match")
      return redirect("/signup?message=Passwords+do+not+match")

    if teacher == "1":
      print("Admin access granted")

    if len(password) < 8:
      return redirect("/signup?message=Password+must+be+at+least+8+characters")

    hashed_password = bcrypt.generate_password_hash(
        password)  #creating a hash password
    print(hashed_password)
    con = create_connection(DATABASE)
    query = "INSERT INTO user(fname, lname, email, password) VALUES(?, ?, ?, ?)"
    cur = con.cursor()

    try:
      #run the query
      cur.execute(query, (fname, lname, email, hashed_password))
    except sqlite3.IntegrityError:
      con.close()
      return redirect('/signup?message=Email+is+already+used')

    con.commit()
    con.close()

    return redirect("/login")

  message = request.args.get("message")
  print(message)
  if message is None:
    message = ""

  return render_template('signup.html',
                         logged_in=is_logged_in(),
                         is_teacher=is_teacher(),
                         message=message)


#functions to modify data in the database
def get_list(query, parameters):
  """List of data without parameters"""
  con = create_connection(DATABASE)
  cur = con.cursor()
  if parameters == "":
    cur.execute(query)
  else:
    cur.execute(query, parameters)
  query_list = cur.fetchall()
  con.close()
  return query_list


def put_data(query, parameters):
  """Update database with parameters"""
  con = create_connection(DATABASE)
  cur = con.cursor()
  cur.execute(query, parameters)
  con.commit()
  con.close()


#admin page
@app.route('/admin')
def render_admin_page():
  if not is_logged_in():
    return redirect('/message=Need+to+be+logged+in.')

  con = create_connection(DATABASE)
  #fetch the categories
  query = "SELECT * FROM categories"
  cur = con.cursor()
  cur.execute(query)
  category_list = cur.fetchall()

  #fetch the words
  query = "SELECT * FROM words"
  cur.execute(query)
  word_list = cur.fetchall()
  print(word_list)

  con.close()

  message = request.args.get('message')
  print(message)
  if message is None:
    message = ""

  return render_template("admin.html",
                         logged_in=is_logged_in(),
                         categories=category_list,
                         words=word_list,
                         is_teacher=is_teacher(),
                         message=message)


#adding a category function
@app.route('/add_category', methods=['POST'])
def add_category():
  if not is_logged_in():
    return redirect('/message=Need+to+be+logged+in.')
  if request.method == "POST":
    print(request.form)
    cat_name = request.form.get('category').lower().strip()
    print(cat_name)
    con = create_connection(DATABASE)
    query = "INSERT INTO categories ('category_name') VALUES (?)"
    cur = con.cursor()
    cur.execute(query, (cat_name, ))
    con.commit()
    con.close()

  return redirect('/admin?message=Category+added+successfully')

  message = request.args.get('message')
  print(message)
  if message is None:
    message = ""

  return render_template("admin.html", message=message)
  return redirect('/admin')


#deleting a category function
@app.route('/delete_category', methods=['POST'])
def render_delete_category():
  if not is_logged_in():
    return redirect('/message=Need+to+be+logged+in.')

  if request.method == "POST":
    con = create_connection(DATABASE)
    category = request.form.get('category_id')
    print(category)
    category = category.split(", ")
    cat_id = category[0]
    cat_name = category[1]

  message = request.args.get('message')
  print(message)
  if message is None:
    message = ""

    return render_template("delete_confirm.html",
                           id=cat_id,
                           name=cat_name,
                           type='category',
                           message=message)
  return redirect("/admin")


#confirmation of delete category
@app.route('/delete_category_confirm/<int:cat_id>')
def render_delete_category_confirm(cat_id):
  if not is_logged_in():
    return redirect('/message=Need+to+be+logged+in.')
  con = create_connection(DATABASE)
  query = "DELETE FROM categories WHERE category_id = ?"
  cur = con.cursor()
  cur.execute(query, (cat_id, ))
  con.commit()
  con.close()
  return redirect('/admin?message=Category+deleted+successfully')

  message = request.args.get('message')
  print(message)
  if message is None:
    message = ""

  return render_template("admin.html", message=message)

  return redirect("/admin")


#adding an word
@app.route('/add_word', methods=['POST'])
def render_add_word():
  if not is_logged_in():
    return redirect('/message=Need+to+be+logged+in.')
  if request.method == "POST":
    print(request.form)
    english = request.form.get('english').lower().strip()
    word_description = request.form.get('description').strip()
    cat_id = request.form.get('cat_id').strip()
    level = request.form.get('level').strip()
    image_new = request.form.get('image').strip()
    maori = request.form.get('maori').strip()
    alt = request.form.get('alt_text').lower().strip()

    if os.path.isfile('/static/images/image_new.jpg'):
      print("file exists")  #image exists
    else:
      print("file doesn't exist")
      image_new = "image"  #if image not available, set default image

    if alt == "":
      alt = "placeholder image"
      print("Alt text was not set, and will be set as default")
    else:
      pass

    user_id = session['user_id']
    print(user_id)

    print(english, word_description, cat_id, level, image_new, alt)
    con = create_connection(DATABASE)
    query = "INSERT INTO words ('english_word', 'maori_word', 'description', 'user_id', 'image', 'category_id', 'image', 'level', alt_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    cur = con.cursor()
    cur.execute(query, (english, maori, word_description, user_id, image_new,
                        cat_id, image_new, level, alt))
    con.commit()
    con.close()

  return redirect('/admin?message=Word+added+successfully')

  message = request.args.get('message')
  print(message)
  if message is None:
    message = ""

  return redirect('/admin')


#deleting a word function
@app.route('/delete_word', methods=['POST'])
def render_delete_word():
  if not is_logged_in():
    return redirect('/message=Need+to+be+logged+in.')

  if request.method == "POST":
    con = create_connection(DATABASE)
    words = request.form.get('word_id')
    print(words)
    if words is None:
      return redirect("/admin?message=No+word+selected")

    words = words.split(", ")
    word_id = words[0]
    word_name = words[1] if len(
        words) > 1 else ""  #assign an empty string if word_name doesn't exist
    print(word_id, word_name)

    message = request.args.get('message')
    print(message)
    if message is None:
      message = ""

    return render_template("delete_confirm.html",
                           id=word_id,
                           name=word_name,
                           type='word',
                           message=message)
  return redirect("/admin")


#confirm delete word
@app.route('/delete_word_confirm/<int:word_id>')
def render_delete_word_confirm(word_id):
  if not is_logged_in():
    return redirect('/message=Need+to+be+logged+in.')

  con = create_connection(DATABASE)
  query = "DELETE FROM words WHERE word_id = ?"
  cur = con.cursor()
  cur.execute(query, (word_id, ))
  con.commit()
  print("Test: ", word_id)
  con.close()
  return redirect('/admin?message=Word+deleted+successfully')

  message = request.args.get('message')
  print(message)
  if message is None:
    message = ""

  return render_template("admin.html", message=message)

  return redirect("/admin")


#more info page
@app.route('/more_info/<int:word_id>')
def render_more_page(word_id):
  if not is_logged_in():
    return redirect('/message=Need+to+be+logged+in.')
  con = create_connection(DATABASE)
  query = "SELECT * from words WHERE word_id = ?"
  cur = con.cursor()
  cur.execute(query, (word_id, ))
  info = cur.fetchone()
  id = info[4]
  user = "SELECT fname FROM user WHERE user_id = ?"
  cur.execute(user, (id, ))
  name = cur.fetchone()[0]

  cat_id = info[5]
  category = "SELECT category_name FROM categories WHERE category_id = ?"
  cur.execute(category, (cat_id, ))
  cat = cur.fetchone()[0]

  maximum = "SELECT MAX(word_id) FROM words"
  cur.execute(maximum)
  max = cur.fetchone()[0]

  print("Person who added the word:", name)
  con.commit()
  con.close()

  message = request.args.get('message')
  print(message)
  if message is None:
    message = ""

  return render_template('/more_info.html',
                         word=word_id,
                         word_info=info,
                         user=name,
                         cat=cat,
                         max_id=max,
                         message=message,
                         logged_in=is_logged_in(),
                         is_teacher=is_teacher())


#deleting specific word
@app.route('/delete', methods=['POST'])
def render_delete():
  if not is_logged_in():
    return redirect('/message=Need+to+be+logged+in.')

  if request.method == "POST":
    con = create_connection(DATABASE)
    word = request.form.get('word_id')
    print("Word is", word)
    if word is None:
      return redirect("/admin?error=No+word+selected")

    word = word.split(", ")
    word_id = word[0]
    word_name = word[1] if len(
        word) > 1 else ""  #assign an empty string if word_name doesn't exist
    print(word_id, word_name)

  message = request.args.get('message')
  print(message)
  if message is None:
    message = ""

    return render_template("delete_confirm.html",
                           id=word_id,
                           name=word_name,
                           type='word',
                           message=message)
  return redirect("/admin")


#about function
@app.route('/about')
def render_about_page():

  message = request.args.get('message')
  print(message)
  if message is None:
    message = ""

  return render_template('about.html',
                         message=message,
                         logged_in=is_logged_in(),
                         is_teacher=is_teacher())


if __name__ == "__main__":
  app.run(host='0.0.0.0', port=81)
