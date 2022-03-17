import sqlite3
from sqlite3 import Error
from flask import Flask, render_template, request, redirect, session


from flask_bcrypt import Bcrypt




DB_NAME = "smile.db"

app = Flask(__name__)

bcrypt = Bcrypt(app)
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
        password = request.form["password"].strip()
        session["log in details"] = [email, password]
        con = create_connection(DB_NAME)

        query = """SELECT id, first_name, password FROM user WHERE email = ?"""

        cur = con.cursor()

        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        try:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            db_password = user_data[0][2]

        except IndexError:
            return redirect("/login?error=Email+or+password+is+incorrect")

        if not bcrypt.check_password_hash(db_password, password):

            return redirect("/login?error=Email+or+password+is+incorrect")

        session["email"] = email
        session["user_id"] = user_id
        session["first_name"] = first_name
        session.pop("log in details")
        return redirect("/menu")
    log_in_details = session.get("log in details")
    if log_in_details is None:
        log_in_details = ["", ""]


    error = request.args.get("error")

    if error is None:
        error = ""

    return render_template("login.html", error=error, logged_in = is_logged_in(), details = log_in_details)


@app.route('/signup', methods=["POST", "GET"])
def render_signup():

    if is_logged_in():
        return redirect("/")

    if request.method == "POST":

        fname = request.form.get("fname").title().strip()
        lname = request.form.get("lname").title().strip()
        email = request.form.get("email").title().lower()
        password = request.form.get("password").strip()
        password2 = request.form.get("password2").strip()

        session["sign up details"] = [fname, lname, email, password, password2]

        incorrect_characters_string = """<>{}[]\/,|"""

        if len(fname) < 2:
            return redirect("/signup?error=First+name+needs+at+least+2+characters+or+more")

        if len(lname) < 2:
            return redirect("/signup?error=Last+name+needs+at+least+2+characters+or+more")

        for char in incorrect_characters_string:

            if char in fname or char in lname:

                return redirect("/signup?error=Invalid+characters+in+first+or+last+name")

        if len(email) < 6:
            return redirect("/signup?error=Email+must+be+at+least+6+characters+or+more")

        if password != password2:
            return redirect("/signup?error=Passwords+dont+match")

        if len(password) < 8:
            return redirect("/signup?error=Password+must+be+8+characters+or+more")

        hashed_password = bcrypt.generate_password_hash(password)

        con = create_connection(DB_NAME)

        query = "INSERT INTO user(id, first_name, last_name, email, password) VALUES(Null, ?, ?, ?, ?)"

        cur = con.cursor()

        try:

            cur.execute(query, (fname, lname, email, hashed_password))

        except sqlite3.IntegrityError:
            return redirect("/signup?error=Email+is+already+used?details={}")

        con.commit()

        con.close()

        [session.pop(key) for key in list(session.keys())]
        print(session)
        return redirect("login")
    signup_details = session.get("sign up details")


    if signup_details is None:
        signup_details = ["", "", "", "", ""]

    error = request.args.get("error")

    if error is None:
        error = ""


    return render_template("signup.html", error = error, logged_in = is_logged_in(), details = signup_details)


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


