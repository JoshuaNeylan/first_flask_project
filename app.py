import sqlite3

from flask import Flask, render_template, request, redirect, session

DB_NAME = "smile.db"

app = Flask(__name__)
app.secret_key = "sdjfi3939j93@()@jJIDJijS)09"

def create_connection(db_file):

    try:

        connection = sqlite3.connect(db_file)

        return connection

    except Error as e:
        print(e)

    return None



@app.route('/')
def render_home():
    return render_template("Home.html", logged_in = is_logged_in())


@app.route('/menu')
def render_menu():

    con = create_connection(DB_NAME)

    query = "SELECT name, description, volume, price, image, image_type FROM product"

    cur = con.cursor()
    cur.execute(query)
    product_list = cur.fetchall()
    con.close()







    return render_template("Menu.html", products = product_list, logged_in = is_logged_in())

@app.route('/contact')
def render_contact():
    return render_template("Contact.html", logged_in = is_logged_in())

@app.route('/login', methods=["POST", "GET"])
def render_login():

    if is_logged_in():
       return redirect("/")

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip().lower()
        con = create_connection(DB_NAME)

        query = """SELECT id, first_name FROM user WHERE email = ? AND password  = ?"""

        cur = con.cursor()

        cur.execute(query, (email, password))
        user_data = cur.fetchall()
        con.close()

        if user_data:

            user_id = user_data[0][0]
            first_name = user_data[0][1]


            session["email"] = email
            session["user_id"] = user_id
            session["first_name"] = first_name



            return redirect("/menu")

        else:

            return redirect("/login?error=Email+or+password+is+incorrect")

    error = request.args.get("error")
    if error == None:
        error = ""

    return render_template("login.html", error=error, logged_in = is_logged_in())




@app.route('/signup', methods=["POST", "GET"])
def render_signup():

    if is_logged_in():
        return redirect("/")

    if request.method == "POST":
        print(request.form)
        fname = request.form.get("fname").title().strip()
        lname = request.form.get("lname").title().strip()
        email = request.form.get("email").title().lower()
        password = request.form.get("password")
        password2 = request.form.get("password2")

        if password != password2:
            print(password, password2)
            return redirect("/signup?error=Passwords+dont+match")

        if len(password) < 8:
            return redirect("/signup?error=Password+must+be+8+characters+or+more")




        con = create_connection(DB_NAME)

        query = "INSERT INTO user(id, first_name, last_name, email, password) VALUES(Null, ?, ?, ?, ?)"

        cur = con.cursor()

        try:

            cur.execute(query, (fname, lname, email, password))

        except sqlite3.IntegrityError:
            return redirect("/signup?error=Email+is+already+used")


        con.commit()
        con.close()
        return redirect("\login")

    error = request.args.get("error")
    if error == None:
        error = ""

    return render_template("signup.html", error = error, logged_in = is_logged_in())


def is_logged_in():
    if session.get("email") is None:
        return False


    return True


@app.route("/logout")
def logout():
    [session.pop(key) for key in list(session.keys())]

    return redirect("/?message=See+you+next+time!")


app.run(host="0,0,0,0", debug="True")
# to fix database issue open database right click on smile go into properties and change url from joshua to 18163
# the opposite is done from home

