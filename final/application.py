import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/", methods = ["GET", "POST"])
@login_required
def index():
    """Show portfolio of stocks"""
    if request.method == "GET":
        fields = db.execute("SELECT field FROM fields WHERE user_id = :id", id = session["user_id"])

        return render_template("index.html",fields = fields)
    else:
        field = request.form.get("field")
        mains = db.execute("SELECT username,password FROM passwords WHERE field = :field AND user_id = :id ", field = field, id = session["user_id"])

        if len(mains) != 0:
            return render_template("passwords.html",mains = mains, field = field)
        else:
            return render_template("no_pass.html")

    return apology("TODO")


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("add.html")
    else:
        field = request.form.get("field")

        if field == "":
            return apology("Not valid")

        fields = db.execute("SELECT * FROM fields WHERE field = :field and user_id= :id",field = field, id = session["user_id"])

        if len(fields) == 1:
            return apology("Field already exists",309)

        db.execute("INSERT INTO fields (field, user_id) VALUES(:field, :id)", field = field, id = session["user_id"])

        return redirect("/")
        pass
    return apology("TODO")


@app.route("/remove_field", methods = ["GET","POST"])
@login_required
def remove_field():
    """Show history of transactions"""

    if request.method == "GET":
        fields = db.execute("SELECT field FROM fields WHERE user_id = :id", id = session["user_id"])

        return render_template("remove_field.html",fields = fields)
    else:
        field = request.form.get("field")

        db.execute("DELETE FROM fields WHERE field = :field AND user_id = :id", field = field, id = session["user_id"])

        return redirect("/")

@app.route("/remove_password", methods = ["GET","POST"])
@login_required
def remove_password():
    """Show history of transactions"""
    if request.method == "GET":
        fields = db.execute("SELECT field FROM fields WHERE user_id = :id", id = session["user_id"])

        return render_template("remove_password.html", fields = fields)

    else:
        field = request.form.get("field")
        usr = request.form.get("username")


        user = db.execute("SELECT username FROM passwords WHERE field = :field AND user_id = :id AND username=:user",user=usr, field = field, id = session["user_id"])

        if len(user) != 1:
            return apology("Username Not found")

        db.execute("DELETE FROM passwords WHERE field = :field AND username = :usr AND user_id = :id",
                    id = session["user_id"],
                    field = field,
                    usr = usr,
                    )

        return redirect("/")

    return apology("TODO")

@app.route("/edit_password", methods = ["GET","POST"])
@login_required
def edit_password():
    """Show history of transactions"""
    if request.method == "GET":
        fields = db.execute("SELECT field FROM fields WHERE user_id = :id", id = session["user_id"])

        return render_template("edit_password.html", fields = fields)

    else:
        field = request.form.get("field")
        usr = request.form.get("username")
        passw = request.form.get("password")

        user = db.execute("SELECT username FROM passwords WHERE field = :field AND user_id = :id AND username = :usr",usr=usr, field = field, id = session["user_id"])

        if len(user) != 1:
            return apology("Username Not Found")
        else:
            db.execute("UPDATE passwords SET password = :passw WHERE user_id = :id AND username = :usr AND field = :field",
                    passw = passw,
                    id = session["user_id"],
                    usr = usr,
                    field = field)

            return  redirect("/")


    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    """Get stock quote."""
    return render_template("edit.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        usr = request.form.get("username")
        passw = request.form.get("password")
        conf = request.form.get("confirmation")

        rows = db.execute("SELECT * FROM users WHERE username = :user",user=usr)

        if usr == "":
            return apology("Please Enter A Username",202)
        elif len(rows) == 1:
            return apology("Username already exists",203)

        if passw == "":
            return apology("Please enter Password",300)
        elif passw != conf:
            return apology("Passwords do not match",301)

        hashed_pass = generate_password_hash(passw)

        db.execute("INSERT INTO users (username,hash) VALUES(:usr,:passw)",usr = usr, passw = hashed_pass)

        return redirect("/")



@app.route("/add_pass", methods=["GET", "POST"])
@login_required
def add_pass():
    """Sell shares of stock"""
    if request.method == "GET":
        fields = db.execute("SELECT field FROM fields WHERE user_id = :id", id = session["user_id"])

        return render_template("add_pass.html",fields = fields)

    else:
        field = request.form.get("field")
        usr = request.form.get("username")
        passw = request.form.get("password")

        db.execute("INSERT INTO passwords (user_id, field, username, password) VALUES(:user_id, :field, :usr, :passw)",
                    user_id = session["user_id"],
                    field = field,
                    usr = usr,
                    passw = passw)

        return redirect("/")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
#pk_1d8b33e8e4b541aaadb75091fc3cfd71