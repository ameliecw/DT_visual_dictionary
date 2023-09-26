from flask import Flask, redirect, render_template, request
import sqlite3
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
  return session.get("email") is not None


#user is teacher or not
def is_teacher():
  #check if the teacher checkbox was ticked
  if session.get("teacher") == 1:
    #check if email contains 'student' no admin access
    if session.get("email").find("student") != -1:
      return False
    else:
      return True
  else:
    return False


#home page function
@app.route('/')
def render_homepage():

  message = request.args.get("message")
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
  category_list = get_list("SELECT * FROM categories ORDER BY category_name",
                           "")
  #fetch the words
  word_list = get_list(
      "SELECT * FROM words WHERE category_id = ? ORDER BY word_id",
      [category_id])
  level_list = get_list("SELECT DISTINCT level FROM words ORDER BY level ASC",
                        "")
  #get categories
  query = "SELECT * FROM categories"
  con = create_connection(DATABASE)
  cur = con.cursor()
  cur.execute(query)
  category_list = cur.fetchall()

  #get words
  query = "SELECT * FROM words WHERE category_id = ? ORDER BY word_id"
  cur.execute(query, (category_id, ))
  word_list = cur.fetchall()
  con.close()

  #return to main words page if no words found
  if not word_list:
    return redirect("/words/1?message=No+words+in+that+category")

  message = request.args.get('message')
  if message is None:
    message = ""

  return render_template('words.html',
                         categories=category_list,
                         words=word_list,
                         levels=level_list,
                         logged_in=is_logged_in(),
                         is_teacher=is_teacher(),
                         message=message)


#search through words
@app.route('/words', methods=['POST'])
def search():
  category_list = get_list("SELECT * FROM categories", "")
  level_list = get_list("SELECT DISTINCT level FROM words ORDER BY level ASC",
                        "")
  if request.method == "POST":
    search = request.form.get('search').lower().strip()

    con = create_connection(DATABASE)
    query = """SELECT * FROM words WHERE english_word LIKE ? OR maori_word LIKE ? OR 
    description LIKE ? ORDER BY english_word"""
    cur = con.cursor()
    cur.execute(query, (
        '%' + search + '%',
        '%' + search + '%',
        '%' + search + '%',
    ))
    result = cur.fetchall()  #only one value
    con.close()

  message = request.args.get('message')
  if message is None:
    message = ""

  return render_template('words.html',
                         logged_in=is_logged_in(),
                         is_teacher=is_teacher(),
                         words=result,
                         levels=level_list,
                         categories=category_list,
                         message=message)


#search with the levels
@app.route('/levels', methods=['POST'])
def level():
  category_list = get_list("SELECT * FROM categories", "")
  level_list = get_list("SELECT DISTINCT level FROM words ORDER BY level ASC",
                        "")
  if request.method == "POST":
    levels = request.form.get('level')

    con = create_connection(DATABASE)
    query = "SELECT * FROM words WHERE level = ? ORDER BY word_id"
    cur = con.cursor()
    cur.execute(query, (levels, ))
    level_result = cur.fetchall()  #only one value
    con.close()

  message = request.args.get('message')
  if message is None:
    message = ""

  return render_template('words.html',
                         logged_in=is_logged_in(),
                         is_teacher=is_teacher(),
                         words=level_result,
                         categories=category_list,
                         levels=level_list,
                         message=message)


#login function
@app.route('/login', methods=['POST', 'GET'])
def render_login_page():
  if is_logged_in():
    return redirect('/')

  if request.method == 'POST':
    email = request.form['email'].strip().lower()
    password = request.form['password'].strip()

    con = create_connection(DATABASE)
    if con is None:
      print("Failed to connect to the database")

    #initial set up of hashed passwords for database entered users

    #cur = con.cursor()
    #new_hashed_password = generate_password_hash(password)
    #cur.execute("UPDATE user SET password = ? WHERE email = ?",
    #           (new_hashed_password, email))
    #con.commit()
    #con.close()

    query = "SELECT user_id, fname, password, teacher FROM user WHERE email = ?"
    cur = con.cursor()
    cur.execute(query, (email, ))
    user_data = cur.fetchall()  #only one value
    con.close()

    if len(user_data) == 0:
      return redirect("/login?message=Email+invalid+or+password+incorrect")

    try:
      user_id = user_data[0][0]
      first_name = user_data[0][1]
      db_password = user_data[0][2]
      teacher = user_data[0][3]
    except IndexError:
      return redirect("/login?message=Email+invalid+or+password+incorrect")

    if not bcrypt.check_password_hash(db_password, password):
      return redirect("/login?message=Email+invalid+or+password+incorrect")

    session['email'] = email
    session['user_id'] = user_id
    session['firstname'] = first_name
    session['teacher'] = teacher

    return redirect("/?message=Successfully+logged+in")

  message = request.args.get('message')
  if message is None:
    message = ""

  return render_template('login.html',
                         logged_in=is_logged_in(),
                         is_teacher=is_teacher(),
                         message=message)


#logout function
@app.route('/logout')
def logout():
  [session.pop(key) for key in list(session.keys())]
  return redirect('/login?message=Logged+out+securely')

  message = request.args.get('message')
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
    fname = request.form.get('fname').title().strip()
    lname = request.form.get('lname').title().strip()
    email = request.form.get('email').lower().strip()
    teacher = request.form.get('teacher')
    password = request.form.get('password')
    password2 = request.form.get('password2')

    if password != password2:
      return redirect("/signup?message=Passwords+do+not+match")

    if len(password) < 8:
      return redirect("/signup?message=Password+must+be+at+least+8+characters")

    hashed_password = bcrypt.generate_password_hash(
        password)  #creating a hash password
    con = create_connection(DATABASE)
    query = "INSERT INTO user(fname, lname, email, password, teacher) VALUES(?, ?, ?, ?, ?)"
    cur = con.cursor()

    try:
      #run the query
      cur.execute(query, (fname, lname, email, hashed_password, teacher))
    except sqlite3.IntegrityError:
      con.close()
      return redirect('/signup?message=Email+is+already+used')

    con.commit()
    con.close()

    return redirect("/login")

  message = request.args.get("message")
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
    return redirect('/?message=Need+to+be+logged+in.')

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
  con.close()

  message = request.args.get('message')
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
    return redirect('/?message=Need+to+be+logged+in.')
  if request.method == "POST":
    cat_name = request.form.get('category').lower().strip()

    con = create_connection(DATABASE)
    query = "INSERT INTO categories ('category_name') VALUES (?)"
    cur = con.cursor()
    cur.execute(query, (cat_name, ))
    con.commit()
    con.close()

  return redirect('/admin?message=Category+added+successfully')

  message = request.args.get('message')
  if message is None:
    message = ""

  return render_template("admin.html", message=message)
  return redirect('/admin')


#deleting a category function
@app.route('/delete_category', methods=['POST'])
def render_delete_category():
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')

  #retrieving category information from the form
  if request.method == "POST":
    con = create_connection(DATABASE)
    category = request.form.get('category_id')
    category = category.split(", ")
    cat_id = category[0]
    cat_name = category[1]

  message = request.args.get('message')
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
    return redirect('/?message=Need+to+be+logged+in.')
  con = create_connection(DATABASE)
  query = "DELETE FROM categories WHERE category_id = ?"
  cur = con.cursor()
  cur.execute(query, (cat_id, ))
  con.commit()
  con.close()
  return redirect('/admin?message=Category+deleted+successfully')

  message = request.args.get('message')
  if message is None:
    message = ""

  return render_template("admin.html", message=message)

  return redirect("/admin")


#adding an word
@app.route('/add_word', methods=['POST'])
def render_add_word():
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')
  if request.method == "POST":
    english = request.form.get('english').lower().strip()
    word_description = request.form.get('description').strip()
    cat_id = request.form.get('cat_id').strip()
    level = request.form.get('level').strip()
    image_new = request.form.get('image').strip()
    maori = request.form.get('maori').strip()
    alt = request.form.get('alt_text').lower().strip()

    user_id = session['user_id']

    con = create_connection(DATABASE)
    cur = con.cursor()
    query = """INSERT INTO words ('english_word', 'maori_word', 
    'description', 'user_id', 'image', 'category_id', 'image', 
    'level', alt_text, date_added) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 
    (julianday('now')))"""
    cur.execute(query, (
        english,
        maori,
        word_description,
        user_id,
        image_new,
        cat_id,
        image_new,
        level,
        alt,
    ))
    con.commit()
    con.close()

  return redirect('/admin?message=Word+added+successfully')

  message = request.args.get('message')
  if message is None:
    message = ""

  return redirect('/admin')


#deleting a word function
@app.route('/delete_word', methods=['POST'])
def render_delete_word():
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')

  if request.method == "POST":
    words = request.form.get('word_id')
    if words is None:
      return redirect("/admin?message=No+word+selected")

    words = words.split(", ")
    word_id = words[0]
    word_name = words[1] if len(
        words) > 1 else ""  #assign an empty string if word_name doesn't exist

    message = request.args.get('message')
    if message is None:
      message = ""

    return render_template("delete_confirm.html",
                           logged_in=is_logged_in(),
                           is_teacher=is_teacher(),
                           id=word_id,
                           name=word_name,
                           type='word',
                           message=message)
  return redirect("/admin")


#confirm delete word
@app.route('/delete_word_confirm/<int:word_id>')
def render_delete_word_confirm(word_id):
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')

  con = create_connection(DATABASE)
  query = "DELETE FROM words WHERE word_id = ?"
  cur = con.cursor()
  cur.execute(query, (word_id, ))
  con.commit()
  con.close()
  return redirect('/admin?message=Word+deleted+successfully')

  message = request.args.get('message')
  if message is None:
    message = ""

  return render_template("admin.html", message=message)

  return redirect("/admin")


#more info page
@app.route('/more_info/<int:word_id>')
def render_more_page(word_id):
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')
  con = create_connection(DATABASE)
  #fetch the categories
  query = "SELECT * FROM categories"
  cur = con.cursor()
  cur.execute(query)
  category_list = cur.fetchall()
  #fetch the words
  query = "SELECT * from words WHERE word_id = ?"
  cur = con.cursor()
  cur.execute(query, (word_id, ))
  info = cur.fetchone()

  #selecting the user that added the word
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

  #selecting the date from the database
  date_query = "SELECT date(date_added), time(date_added) FROM words WHERE word_id = ?"
  cur.execute(date_query, (word_id, ))
  date = cur.fetchone()[0]

  con.commit()
  con.close()

  message = request.args.get('message')
  if message is None:
    message = ""

  return render_template('/more_info.html',
                         word=word_id,
                         word_info=info,
                         user=name,
                         cat=cat,
                         max_id=max,
                         categories=category_list,
                         last_updated=date,
                         message=message,
                         logged_in=is_logged_in(),
                         is_teacher=is_teacher())


#deleting specific word
@app.route('/delete', methods=['POST'])
def render_delete():
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')

  if request.method == "POST":
    word = request.form.get('word_id')
    if word is None:
      return redirect("/admin?/message=No+word+selected")

    word = word.split(", ")
    word_id = word[0]
    word_name = word[1] if len(
        word) > 1 else ""  #assign an empty string if word_name doesn't exist

  message = request.args.get('message')
  if message is None:
    message = ""

    return render_template("delete_confirm.html",
                           logged_in=is_logged_in(),
                           is_teacher=is_teacher(),
                           id=word_id,
                           name=word_name,
                           type='word',
                           message=message)
  return redirect("/admin")


#make changes to the english for one specific word
@app.route('/modify_english/<int:word_id>', methods=['POST'])
def render_modify_english(word_id):
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')

  if request.method == "POST":
    con = create_connection(DATABASE)
    english = request.form.get('english').lower().strip()
    #if the value from the form is null
    if english is None:
      return redirect('/admin?/message=Please+enter+a+valid+word')
    con = create_connection(DATABASE)
    query = "UPDATE words SET english_word = ? WHERE word_id = ?"
    cur = con.cursor()
    cur.execute(query, (english, word_id))
    con.commit()
    con.close()
    return redirect('/admin?message=English+updated+successfully')

  message = request.args.get('message')
  if message is None:
    message = ""

  return redirect("/admin", message=message)


#make changes to the maori for one specific word
@app.route('/modify_maori/<int:word_id>', methods=['POST'])
def render_modify_maori(word_id):
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')

  if request.method == "POST":
    con = create_connection(DATABASE)
    maori = request.form.get('maori').lower().strip()
    #if the value from the form is null
    if maori is None:
      return redirect('/admin?/message=Please+enter+a+maori+word')
    con = create_connection(DATABASE)
    query = "UPDATE words SET maori_word = ? WHERE word_id = ?"
    cur = con.cursor()
    cur.execute(query, (maori, word_id))
    con.commit()
    con.close()
    return redirect('/admin?message=Maori+updated+successfully')

  message = request.args.get('message')
  if message is None:
    message = ""

  return redirect("/admin", message=message)


#make changes to the description for one specific word
@app.route('/modify_description/<int:word_id>', methods=['POST'])
def render_modify_description(word_id):
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')

  if request.method == "POST":
    con = create_connection(DATABASE)
    description = request.form.get('description').lower().strip()
    if description is None:
      return redirect('/admin?/message=Please+enter+a+description')
    con = create_connection(DATABASE)
    query = "UPDATE words SET description = ? WHERE word_id = ?"
    cur = con.cursor()
    cur.execute(query, (description, word_id))
    con.commit()
    con.close()
    return redirect('/admin?message=Description+updated+successfully')

  message = request.args.get('message')
  if message is None:
    message = ""

  return redirect("/admin", message=message)


#make changes to the level for one specific word
@app.route('/modify_level/<int:word_id>', methods=['POST'])
def render_modify_level(word_id):
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')

  if request.method == "POST":
    con = create_connection(DATABASE)
    level = request.form.get('level')
    #if the value from the form is null
    if level is None:
      return redirect('/admin?/message=Level+selected+incorrectly')
    con = create_connection(DATABASE)
    query = "UPDATE words SET level = ? WHERE word_id = ?"
    cur = con.cursor()
    cur.execute(query, (level, word_id))
    con.commit()
    con.close()
    return redirect('/admin?message=Level+updated+successfully')

  message = request.args.get('message')
  if message is None:
    message = ""

  return redirect("/admin", message=message)


#make changes to the description for one specific word
@app.route('/modify_category/<int:word_id>', methods=['POST'])
def render_modify_category(word_id):
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')

  if request.method == "POST":
    con = create_connection(DATABASE)
    category = request.form.get('category')
    #if the value from the form is null
    if category is None:
      return redirect('/admin?/message=Please+pick+a+category')
    con = create_connection(DATABASE)
    query = "UPDATE words SET category_id = ? WHERE word_id = ?"
    cur = con.cursor()
    cur.execute(query, (category, word_id))
    con.commit()
    con.close()
    return redirect('/admin?message=Category+updated+successfully')

  message = request.args.get('message')
  if message is None:
    message = ""

  return redirect("/admin", message=message)


#make changes to the alt text
@app.route('/modify_alt_text/<int:word_id>', methods=['POST'])
def render_alt_text(word_id):
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')

  if request.method == "POST":
    con = create_connection(DATABASE)
    alt_text = request.form.get('alt_text')
    #if the value from the form is null
    if alt_text == "":
      return redirect('/admin?/message=Please+enter+some+text')
    con = create_connection(DATABASE)
    query = "UPDATE words SET alt_text = ? WHERE word_id = ?"
    cur = con.cursor()
    cur.execute(query, (alt_text, word_id))
    con.commit()
    con.close()
    return redirect('/admin?message=Alt+text+updated+successfully')

  message = request.args.get('message')
  if message is None:
    message = ""

  return redirect("/admin", message=message)


#make changes to the image
@app.route('/modify_image/<int:word_id>', methods=['POST'])
def render_image(word_id):
  if not is_logged_in():
    return redirect('/?message=Need+to+be+logged+in.')

  if request.method == "POST":
    con = create_connection(DATABASE)
    image_get = request.form.get('image').lower().strip()
    #if the value returned from the form is null
    if image_get == "":
      return redirect('/admin?message=Text+was+not+entered+properly')

    image_get = request.form.get('image').lower()
    con = create_connection(DATABASE)
    query = "UPDATE words SET image = ? WHERE word_id = ?"
    cur = con.cursor()
    cur.execute(query, (image_get, word_id))
    con.commit()
    con.close()
    return redirect('/admin?message=Image+updated+successfully')

  message = request.args.get('message')
  if message is None:
    message = ""

  return redirect("/admin", message=message)


if __name__ == "__main__":
  app.run(host='0.0.0.0', port=81)
