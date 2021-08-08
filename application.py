import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
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


@app.route("/")
@login_required
def index():
    portfel = db.execute("SELECT stock, shares from shares WHERE id = :id", id=session["user_id"])
    remain_cash = db.execute("SELECT cash from users WHERE id = :id", id=session["user_id"])

    cash = float(remain_cash[0]["cash"])
    for stock in portfel:
        symbol = stock["stock"]
        stock_symbol = lookup(symbol)
        name = stock_symbol["name"]
        shares = stock["shares"]
        price = stock_symbol["price"]
        total = float(price * shares)
        return render_template("index.html", portfel=portfel, symbol=symbol, name=name, shares=shares, price=price, total=total, cash=cash)
    else:
        return apology("You need to buy something first", 200)



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        if not request.form.get("shares"):
            return apology("Number of shares are needed", 400)
        if not request.form.get("symbol"):
            return apology("Stock symbol is needed", 400)

        symbol = lookup(request.form.get("symbol"))
        stock_symbol = request.form.get("symbol").upper()

        shares = int(request.form.get("shares"))

        if not symbol:
            return apology("Invalid symbol", 400)

        if int(request.form.get("shares")) < 0:
            return apology("Shares must be a positive integer", 400)

        price = symbol["price"]

        portfel = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])
        cash = portfel[0]["cash"]

        shares_worth = cash - int(request.form.get("shares")) * price
        if shares_worth < 0:
            return apology("You don't have enough money", 400)

        db.execute ("UPDATE users SET cash = :shares_worth WHERE id =:session", shares_worth = shares_worth, session = session["user_id"])
        db.execute("INSERT or IGNORE INTO shares (id, stock, shares) VALUES(:session, :symbol, :shares)", session = session["user_id"], symbol = stock_symbol, shares = shares)
        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/", 200)

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Stock symbol is needed")
        symbol = lookup(request.form.get("symbol"))
        if not symbol:
            return apology("Invalid symbol")
        else:
            return render_template("quoted.html", name=symbol["name"], price=symbol["price"], symbol=symbol["symbol"])
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
 if request.method == "POST":

        if not request.form.get("username"):
            return apology("Username is required", 400)
            flash("Username is required")



        elif not request.form.get("password"):
            return apology("Password is required", 400)
            flash("Password is required")

        elif not request.form.get("confirmation"):
            return apology("Password confirmation is required", 400)



        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("Passwords must be identical", 400)

        hash = generate_password_hash(request.form.get("password"))
        try:
            new = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=request.form.get("username"), hash=hash)
        except:
            return apology("You need to buy something first", 400)


        session["user_id"] = new

        return redirect("/")
 else:

        return render_template("register.html")

@app.route("/addfund", methods=["GET", "POST"])
@login_required
def addfund():
    if request.method == "POST":
        portfel = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])
        cash = portfel[0]["cash"]

        if int(request.form.get("funds")) < 0:
            return apology("Funds cannot be a negative number", 400)

        if int(request.form.get("funds")) > 10000:
            return apology("10 000 USD is the limit", 400)
        if not request.form.get("funds"):
            return apology("You must provide a number", 400)
        funds = int(request.form.get("funds"))
        updated_cash = cash + int(request.form.get("funds"))
        db.execute ("UPDATE users SET cash = :updated_cash WHERE id =:session", updated_cash = updated_cash, session = session["user_id"])
        return redirect("/")
    else:
        return render_template("addfund.html")
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
