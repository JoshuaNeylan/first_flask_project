import sqlite3
from sqlite3 import Error
from flask import Flask, render_template, request, redirect, session

from flask_bcrypt import Bcrypt
from datetime import datetime
import ssl, smtplib

from smtplib import SMTPAuthenticationError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DB_NAME = "smile.db"

app = Flask(__name__)

bcrypt = Bcrypt(app)
app.secret_key = "sdjfi3939j93@()@jJIDJijS)09"


def create_connection(db_file):
    try:

        connection = sqlite3.connect(db_file)
        connection.execute("pragma foreign_keys=ON")

        return connection

    except Error as e:
        print(e)

    return None


@app.route('/')
def render_home():
    return render_template("Home.html", logged_in=is_logged_in())


@app.route('/menu')
def render_menu():
    con = create_connection(DB_NAME)

    query = "SELECT name, description, volume, price, image, image_type, id FROM product"

    cur = con.cursor()
    cur.execute(query)
    product_list = cur.fetchall()
    con.close()

    return render_template("Menu.html", products=product_list, logged_in=is_logged_in())


@app.route('/contact')
def render_contact():
    return render_template("Contact.html", logged_in=is_logged_in())


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

    return render_template("login.html", error=error, logged_in=is_logged_in(), details=log_in_details)


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

    return render_template("signup.html", error=error, logged_in=is_logged_in(), details=signup_details)


def is_logged_in():
    if session.get("email") is None:
        return False

    return True


@app.route("/logout")
def logout():
    [session.pop(key) for key in list(session.keys())]

    return redirect("/?message=See+you+next+time!")


@app.route("/addtocart/<product_id>")
def render_add_to_cart(product_id):
    if not is_logged_in():
        return redirect("/")

    try:
        productid = int(product_id)
    except ValueError:
        print(f"{product_id} isn't an interger")
        return redirect("/menu?error=Invalid+product+id")

    print("Added product id {} to the cart".format(product_id))
    customerid = session["user_id"]
    timestamp = datetime.now()

    query = "INSERT INTO cart (customerid, productid, timestamp) VALUES (?, ?, ?)"

    con = create_connection(DB_NAME)
    cur = con.cursor()

    try:
        cur.execute(query, (customerid, product_id, timestamp))

    except sqlite3.IntegrityError as e:
        print(e)
        print("Problem Inserting into database - foreign key!")
        con.close()
        return redirect("/menu?error=Invalid+product+id")

    con.commit()
    con.close()
    return redirect("/menu")


def cart_products_sorter(product_ids, cur):

    for i in range(len(product_ids)):
        product_ids[i] = product_ids[i][0]

    unique_product_ids = list(set(product_ids))

    for i in range(len(unique_product_ids)):
        product_count = product_ids.count(unique_product_ids[i])
        unique_product_ids[i] = [unique_product_ids[i], product_count]

    query = "SELECT name, price FROM product WHERE id = ?;"

    for item in unique_product_ids:
        cur.execute(query, (item[0],))
        item_details = cur.fetchall()
        print(item_details)
        item.append(item_details[0][0])
        item.append(item_details[0][1])

    return unique_product_ids

@app.route("/cart")
def render_cart():
    if not is_logged_in():
        return redirect("/")

    customerid = session["user_id"]
    query = "SELECT productid FROM cart where customerid = ?;"
    con = create_connection(DB_NAME)
    cur = con.cursor()
    cur.execute(query, (customerid,))
    product_ids = cur.fetchall()

    total = 0
    unique_product_ids = cart_products_sorter(product_ids, cur)

    for product in unique_product_ids:

        subtotal = product[3] * product[1]
        total += subtotal

    total = "{:.2f}".format(total)

    con.close()

    print(unique_product_ids)

    return render_template("cart.html", cart_data=unique_product_ids, total = total, logged_in=is_logged_in())


@app.route("/removeonefromcart/<productid>")
def remove_one_from_cart(productid):
    if not is_logged_in():
        return redirect("/")

    print(f"Removed {productid} from cart")
    customerid = session["user_id"]
    query = "DELETE FROM cart WHERE id = (SELECT MIN(id) FROM cart WHERE productid = ? and customerid = ?);"
    con = create_connection(DB_NAME)
    cur = con.cursor()
    cur.execute(query, (productid, customerid,))
    con.commit()
    con.close()

    return redirect("/cart")




@app.route("/confirmorder")
def confirm_order():
    if not is_logged_in():
        return redirect("/")

    customerid = session["user_id"]
    con = create_connection(DB_NAME)
    cur = con.cursor()

    query = "SELECT productid FROM cart WHERE customerid = ?"

    cur.execute(query, (customerid,))

    product_ids = cur.fetchall()

    if len(product_ids) == 0:
        return redirect("/menu?error=Cart+empty")

    unique_product_ids = cart_products_sorter(product_ids, cur)

    query = "DELETE FROM cart WHERE id = ?"

    cur.execute(query, (customerid,))
    con.commit()
    con.close()

    send_confirmation(unique_product_ids)

    return redirect("/?message=Order+complete")


def send_confirmation(order_info):
    print(order_info)
    email = session["email"]
    firstname = session["first_name"]
    SSL_PORT = 465
    # Use test email or another email
    sender_email = "joshwctest@gmail.com"
    sender_password = ".ajVsg/E3Ycx?gM"
    table = "<table>\n<tr><th>Name</th><th>Quantity </th><th>Price</th><th>Order Total</th></tr>\n"
    total = 0
    for product in order_info:
        name = product[2]
        quantity = product[1]
        price = product[3]
        subtotal = product[3] * product[1]
        total += subtotal
        table += "<tr><td>{}</td><td>{}</td><td>${:.2f}</td><td>${:.2f}</td></tr>\n".format(name, quantity, price,
                                                                                          subtotal)
    table += "<tr><td></td><td></td><td>Total:</td><td>${:.2f}</td></tr>\n</table>".format(total)
    print(table)
    print(total)
    html_text = """<p>Hello {}.</p>
       <p>Thank you for shopping at smile cafe. Your order summary:</p>
       {}
       <p>Thank you, <br>The staff at smile cafe.</p>""".format(firstname, table)
    print(html_text)

    context = ssl.create_default_context()
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your order with smile"

    message["From"] = "smile cafe"
    message["To"] = email

    html_content = MIMEText(html_text, "html")
    message.attach(html_content)
    with smtplib.SMTP_SSL("smtp.gmail.com", SSL_PORT, context=context) as server:
        try:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())
        except SMTPAuthenticationError as e:
            print(e)


app.run(host="0,0,0,0", debug="True")
# to fix database issue open database right click on smile go into properties and change url from joshua to 18163
# the opposite is done from home


