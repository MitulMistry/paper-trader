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

# Configure application
app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)

# Configure SQLAlchemy and migrations using Alembic
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
        if User.query.filter_by(username=request.form.get("username")).first() == None:
            return render_template("register.html", error="Username is already taken"), 400

        # Validate email was submitted
        if not request.form.get("email"):
            return render_template("register.html", error="Must provide email"), 400

        # Validate email structure
        email_regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
        if not re.search(email_regex, request.form.get("email")):
            return render_template("register.html", error="Must provide valid email"), 400

        # Validate email uniqueness (doesn't already exist in database)
        if User.query.filter_by(email=request.form.get("email")).first() == None:
            return render_template("register.html", error="Username is already taken"), 400

        # Validate password was submitted
        if not request.form.get("password"):
            return render_template("register.html", error="Must provide password"), 400

        # Validate password confirmation was submitted
        if not request.form.get("confirmation"):
            return render_template("register.html", error="Must provide password confirmation"), 400

        # Validate password matches password confirmation
        if request.form.get("password") != request.form.get("confirmation"):
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
        if not (request.form.get("cash").isnumeric() and request.form.get("cash") >= 100 and request.form.get("cash") <= 10000000):
            return render_template("register.html", error="Must provide valid starting cash amount (between $100 and $10,000,000)"), 400

        # Create user in database        
        new_user = User(
            username=request.form.get("username"),
            email=request.form.get("email"),
            password_hash=generate_password_hash(request.form.get("password")),
            cash=request.form.get("cash")
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
        user = User.query.filter(username=request.form.get("username")).first()

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
def logout():
    """Log user out and clear session"""
    
    # Forget any user_id
    session.clear()

    flash("Logged out")
    return redirect("/")


@app.route("/delete", methods=["DELETE"])
def delete():
    """Delete user account"""
    
    # TODO

    return redirect("/")


@app.route("/buy", methods=["GET", "POST"])
def buy():
    """Buy shares of a stock"""
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # TODO

        return redirect("/portfolio")
    
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/sell", methods=["GET", "POST"])
def sell():
    """Sell shares of a stock"""
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # TODO
        # If 0 shares of stock in portfolio, remove holding from account

        return redirect("/portfolio")
    
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("sell.html")


@app.route("/quote/<string:stock_symbol>")
def quote(stock_symbol):
    """Get stock quote"""

    # TODO
    # Get stock symbol from URL
    # lookup(escape(stock_symbol)) # Escape user input to ensure safety
    # Check for valid stock symbol
    
    return render_template("quote.html")


@app.route("/portfolio")
def portfolio():
    """Show portfolio of user's stock holdings"""

    # TODO

    return render_template("portfolio.html")


@app.route("/history")
def history():
    """Show history of user's transactions"""

    # TODO

    return render_template("history.html")


@app.route("/addcash", methods=["GET", "POST"])
def addcash():
    """Add cash to user's account"""
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # TODO
        # Check for range of cash ($1-$10,000,000)
        # Check if account already has too much cash (> $10,000,000)

        return redirect("/portfolio")
    
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("addcash.html")


@app.route("/reset", methods=["GET", "POST"])
def reset():
    """Reset user's account"""
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # TODO
        # Check for amount of cash to restart account with

        return redirect("/reset")
    
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("reset.html")