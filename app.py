import os
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from markupsafe import escape
import re
from datetime import datetime

from helpers import login_required, lookup, usd

# Configure application
app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)

# Configure SQLAlchemy and migrations using Alembic
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Make sure API keys are set
if not os.environ.get("IEX_API_KEY"):
    raise RuntimeError("IEX_API_KEY not set")

if not os.environ.get("NEWS_API_KEY"):
    raise RuntimeError("NEWS_API_KEY not set")

# Import models for SQLAlchemy
from models import User, Holding, Transaction

@app.route("/")
def index():
    """Show website home page"""
    # iex_key = app.config.get("IEX_KEY")
    # google_news_key = app.config.get("GOOGLE_NEWS_KEY")

    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Validate username was submitted
        if not request.form.get("username"):
            return render_template("register.html", error="Must provide username"), 400 # Status code 400, bad request

        # Validate username uniqueness (doesn't already exist in database)
        if User.query.filter_by(username=request.form.get("username")).first() != None:
            return render_template("register.html", error="Username is already taken"), 400

        # Validate email was submitted
        if not request.form.get("email"):
            return render_template("register.html", error="Must provide email"), 400

        # Validate email structure
        email_regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
        if not re.search(email_regex, request.form.get("email")):
            return render_template("register.html", error="Must provide valid email"), 400

        # Validate email uniqueness (doesn't already exist in database)
        if User.query.filter_by(email=request.form.get("email")).first() != None:
            return render_template("register.html", error="Username is already taken"), 400

        # Validate password was submitted
        if not request.form.get("password"):
            return render_template("register.html", error="Must provide password"), 400

        # Validate password confirmation was submitted
        if not request.form.get("password_confirmation"):
            return render_template("register.html", error="Must provide password confirmation"), 400

        # Validate password matches password confirmation
        if request.form.get("password") != request.form.get("password_confirmation"):
            return render_template("register.html", error="Password must match password confirmation"), 400

        # Validate password structure
        password_regex = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
        if not re.search(password_regex, request.form.get("password")):
            return render_template("register.html", error="Must provide password that follows the rules: At least one number, at least \
                one uppercase and one lowercase character, at least one special symbol, and be between 6 to 20 characters long."), 400

        # Validate starting cash amount was submitted
        if not request.form.get("cash"):
            return render_template("register.html", error="Must provide starting cash amount"), 400

        # Validate starting cash amount fits within bounds
        if not (request.form.get("cash").isdigit() and int(request.form.get("cash")) >= 100 and int(request.form.get("cash")) <= 10000000):
            return render_template("register.html", error="Must provide valid starting cash amount (between $100 and $10,000,000)"), 400

        # Create user in database
        new_user = User(
            username=request.form.get("username"),
            email=request.form.get("email"),
            password_hash=generate_password_hash(request.form.get("password")),
            cash=int(request.form.get("cash"))
        )
        db.session.add(new_user)
        db.session.commit()

        # Remember which user has logged in
        session["user_id"] = User.query.filter_by(username=request.form.get("username")).first().id

        # Redirect user to their portfolio
        flash("Account successfully created")
        return redirect("/portfolio")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in and create session"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", error="Must provide username"), 400

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", error="Must provide password"), 400

        # Query database for username
        user = User.query.filter_by(username=request.form.get("username")).first()

        # Ensure username exists and password is correct
        if user == None or not check_password_hash(user.password_hash, request.form.get("password")):
            return render_template("login.html", error="Invalid username and/or password"), 403

        # Remember which user has logged in
        session["user_id"] = user.id

        flash("Logged in as " + user.username)
        return redirect("/portfolio")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Log user out and clear session"""

    # Forget any user_id
    session.clear()

    flash("Logged out")
    return redirect("/")


@app.route("/delete", methods=["DELETE"])
@login_required
def delete():
    """Delete user account"""

    user = User.query.get(session["user_id"])

    db.session.delete(user)
    db.session.delete(user.holdings)
    db.session.delete(user.transactions)
    db.session.commit()

    flash("Account successfully deleted")
    return redirect("/")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of a stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Validate length and alphabetical nature of symbol string
        if not (len(request.form.get("symbol")) <= 5 and request.form.get("symbol").isalpha()):
            return render_template("buy.html", error="Invalid symbol"), 400

        quote = lookup(request.form.get("symbol"))

        # Check if the symbol entry is valid
        if not quote:
            return render_template("buy.html", error="Invalid symbol"), 400

        # Check if shares entry is numeric
        elif not (request.form.get("shares")).isdigit():
            return render_template("buy.html", error="Invalid entry"), 400

        # Check if shares entry is an integer
        elif not float(request.form.get("shares")).is_integer():
            return render_template("buy.html", error="Invalid entry"), 400

        # Check if shares entry is non-negative
        elif int(request.form.get("shares")) <= 0:
            return render_template("buy.html", error="Share bought must be greater than zero"), 400

        # Check if user has enough money to complete purchase of shares
        user = User.query.get(session["user_id"])

        if quote["price"] * int(request.form.get("shares")) > user.cash:
            return render_template("buy.html", error="Not enough cash to complete purchase"), 400

        # Record transaction in database
        new_transaction = Transaction(
            user_id=user.id,
            symbol=quote["symbol"],
            shares=int(request.form.get("shares")),
            price=quote["price"],
            timestamp=datetime.now(),

        )
        db.session.add(new_transaction)

        # Deduct cash from user
        user.cash -= quote["price"] * int(request.form.get("shares"))

        # Update user's stock holdings (portfolio)
        # Check if stock is already in holdings
        found_holding = Holding.query.filter((Holding.user_id == user.id) & (Holding.symbol == new_transaction.symbol)).first()

        # Add stock to holdings if not already owned
        if found_holding == None:
            new_holding = Holding(
                user_id=user.id,
                symbol=new_transaction.symbol,
                shares=new_transaction.shares
            )
            db.session.add(new_holding)

        # Update stock in holdings if already owned
        else:
            found_holding.shares += new_transaction.shares

        # Save all changes to database
        db.session.commit()

        flash("Purchase completed")
        return redirect("/portfolio")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of a stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Validate length and alphabetical nature of symbol string
        if not (len(request.form.get("symbol")) <= 5 and request.form.get("symbol").isalpha()):
            return render_template("sell.html", error="Invalid symbol"), 400

        quote = lookup(request.form.get("symbol"))

        # Check if the symbol entry is valid
        if not quote:
            return render_template("sell.html", error="Invalid symbol"), 400

        # Check if shares entry is numeric
        elif not (request.form.get("shares")).isdigit():
            return render_template("sell.html", error="Invalid entry"), 400

        # Check if shares entry is an integer
        elif not float(request.form.get("shares")).is_integer():
            return render_template("sell.html", error="Invalid entry"), 400

        # Check if shares entry is non-negative
        elif int(request.form.get("shares")) < 0:
            return render_template("sell.html", error="share sold must be greater than zero"), 400

        # Query database to find stock in user's holdings
        user = User.query.get(session["user_id"])
        holding = Holding.query.filter(Holding.user_id==user.id & Holding.symbol==quote["symbol"])

        # Check if user owns shares of stock user wants to sell
        if holding == None:
            return render_template("sell.html", error="You do not own shares in this company"), 400

        # Check if user owns enough shares user intends to sell
        elif holding.shares < int(request.form.get("shares")):
            return render_template("sell.html", error="You do not own that many shares to sell"), 400

        # Record transaction
        new_transaction = Transaction(
            user_id=user.id,
            symbol=quote["symbol"],
            shares=int(request.form.get("shares")) * (-1),
            price=quote["price"],
            timestamp=datetime.now()
        )

        # Add funds from sale to user's account
        user.cash += (int(request.form.get("shares")) * quote["price"])

        # If selling all stock, delete from holdings
        if holding.shares == new_transaction.shares:
            db.session.delete(holding)

        # Otherwise, update the holding row for the stock in the database
        else:
            holding.shares -= new_transaction.shares

        # Save all changes to database
        db.session.commit()

        flash("Sale completed")
        return redirect("/portfolio")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("sell.html")


@app.route("/quote/<string:stock_symbol>", methods=["GET, POST"])
def quote(stock_symbol):
    """Get stock quote"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        symbol = request.form.get("symbol")

    # User reached route via GET (as by clicking a link or via redirect)
    # Get stock symbol from URL, escape user input to ensure safety
    else:
        symbol = escape(stock_symbol)

    # Validate length and alphabetical nature of symbol string
    if not (len(symbol) <= 5 and symbol.isalpha()):
        return render_template("index.html", error="Invalid symbol"), 400

    quote = lookup(symbol)

    if not quote:
        return render_template("index.html", error="Invalid symbol"), 400
    else:
        return render_template("quote.html", quote=quote)


@app.route("/portfolio")
@login_required
def portfolio():
    """Show portfolio of user's stock holdings"""

    # Query database for current user's stock holdings (portfolio)
    user = User.query.get(session["user_id"])
    stocks = user.holdings

    # Get current prices for stocks using API
    for stock in stocks:
        quote = lookup(stock["symbol"])
        stock["price"] = quote["price"]
        stock["shares"] = int(stock["shares"])
        stock["total"] = stock["price"] * stock["shares"]

    # Query database for current user's cash
    cash = user.cash

    return render_template("portfolio.html", stocks=stocks, cash=cash)


@app.route("/history")
@login_required
def history():
    """Show history of user's transactions"""

    # Query database for all transactions made by current user
    user = User.query.get(session["user_id"])
    transactions = user.transactions

    return render_template("history.html", transactions=transactions)


@app.route("/addcash", methods=["GET", "POST"])
@login_required
def addcash():
    """Add cash to user's account"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Validate cash amount was submitted
        if not request.form.get("cash"):
            return render_template("addcash.html", error="Must provide a cash amount to add to account"), 400

        # Validate cash amount fits within bounds ($1-$10,000,000)
        if not (request.form.get("cash").isdigit() and int(request.form.get("cash")) >= 1 and int(request.form.get("cash")) <= 10000000):
            return render_template("addcash.html", error="Must provide valid cash amount to add (between $1 and $10,000,000)"), 400

        # Validate account doesn't already have too much cash (> $10,000,000)
        user = User.query.get(session["user_id"])

        if not (user.cash >= 10000000):
            return render_template("addcash.html", error="Account already has too much cash ($10,000,000 or more)"), 400

        # Validate account won't end up with too much cash (> $10,000,000)
        if not ((user.cash + int(request.form.get("cash"))) >= 10000000):
            return render_template("addcash.html", error="Amount entered would lead the account to have too much cash ($10,000,000 or more). Please enter a lower amount."), 400

        user.cash += int(request.form.get("cash"))
        db.session.commit

        flash("Cash amount added successfully")
        return redirect("/portfolio")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("addcash.html")


@app.route("/reset", methods=["GET", "POST"])
@login_required
def reset():
    """Reset user's account"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Validate cash amount was submitted
        if not request.form.get("cash"):
            return render_template("reset.html", error="Must provide a cash amount to restart account with"), 400

        # Validate starting cash amount fits within bounds
        if not (request.form.get("cash").isdigit() and int(request.form.get("cash")) >= 100 and int(trequest.form.get("cash")) <= 10000000):
            return render_template("register.html", error="Must provide valid starting cash amount (between $100 and $10,000,000)"), 400

        user = User.query.get(session["user_id"])

        user.cash = int(request.form.get("cash"))
        db.session.delete(user.holdings)
        db.session.delete(user.transactions)
        db.session.commit()

        flash("Account successfully reset")
        return redirect("/reset")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("reset.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("index.html", error=e.name + " " + e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)