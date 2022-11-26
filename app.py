import os
from flask import Flask, flash, redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy as _BaseSQLAlchemy
from flask_migrate import Migrate
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from markupsafe import escape
import re
from datetime import datetime
import warnings

from flask_login import (
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

from helpers import lookup, get_news, usd

# Subclass SQLAlchemy to fix psycopg2 operational error on deployment
# https://stackoverflow.com/questions/55457069/how-to-fix-operationalerror-psycopg2-operationalerror-server-closed-the-conn
class SQLAlchemy(_BaseSQLAlchemy):
    def apply_pool_defaults(self, app, options):
        super(SQLAlchemy, self).apply_pool_defaults(self, app, options)
        options["pool_pre_ping"] = True

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

# Flask-Login setup (for sessions)
login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.init_app(app)

# Make sure API keys are set
if not os.environ.get("IEX_API_KEY"):
    warnings.warn("IEX_API_KEY not set")
    # raise RuntimeError("IEX_API_KEY not set")

if not os.environ.get("NEWS_API_KEY"):
    warnings.warn("NEWS_API_KEY not set")
    # raise RuntimeError("NEWS_API_KEY not set")

# Access API keys in routes
# IEX_API_KEY = app.config.get("IEX_API_KEY")
# NEWS_API_KEY = app.config.get("NEWS_API_KEY")

# Import models for SQLAlchemy
from models import User, Holding, Transaction

# Set up user loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Inject current date and time into routes (for copyright year)
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.route("/")
def index():
    """Show website home page"""

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
            return render_template("register.html", error="Email is already taken"), 400

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
        user = User.query.filter_by(username=new_user.username).first()
        login_user(user)

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
    logout_user()

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
        login_user(user)

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
    logout_user()

    flash("Logged out")
    return redirect("/")


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    """Update user info"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        user = current_user
        changes_made = False

        # Check if username was submitted and isn't the same
        if request.form.get("username") and request.form.get("username") != user.username:

            # Validate username uniqueness (doesn't already exist in database)
            if User.query.filter_by(username=request.form.get("username")).first() != None:
                return render_template("update.html", user=user, error="Username is already taken"), 400

            user.username = request.form.get("username")
            changes_made = True

        # Check if email was submitted and isn't the same
        if request.form.get("email") and request.form.get("email") != user.email:

            # Validate email structure
            email_regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
            if not re.search(email_regex, request.form.get("email")):
                return render_template("update.html", user=user, error="Must provide valid email"), 400

            # Validate email uniqueness (doesn't already exist in database)
            if User.query.filter_by(email=request.form.get("email")).first() != None:
                return render_template("update.html", user=user, error="Email is already taken"), 400

            user.email = request.form.get("email")
            changes_made = True

        # Check if password was submitted
        if request.form.get("password"):

            # Validate password confirmation was submitted
            if not request.form.get("password_confirmation"):
                return render_template("update.html", user=user, error="Must provide password confirmation"), 400

            # Validate password matches password confirmation
            if request.form.get("password") != request.form.get("password_confirmation"):
                return render_template("update.html", user=user, error="Password must match password confirmation"), 400

            # Validate password structure
            password_regex = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
            if not re.search(password_regex, request.form.get("password")):
                return render_template("update.html", user=user, error="Must provide password that follows the rules: At least one number, at least \
                    one uppercase and one lowercase character, at least one special symbol, and be between 6 to 20 characters long."), 400

            user.password_hash = generate_password_hash(request.form.get("password"))
            changes_made = True

        # Save changes to database (if changes made)
        if changes_made:
            db.session.commit()
            flash("Account info updated")
        else:
            flash("No changes made")

        return redirect("/portfolio")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        user = current_user
        return render_template("update.html", user=user)


@app.route("/delete", methods=["DELETE"])
@login_required
def delete():
    """Delete user account"""

    user = current_user

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
        user = current_user

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


@app.route("/buy/<string:symbol>")
@login_required
def buy_symbol(symbol):
    return render_template("buy.html", symbol=escape(symbol))


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
        user = current_user
        holding = Holding.query.filter((Holding.user_id==user.id) & (Holding.symbol==quote["symbol"])).first()

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
        db.session.add(new_transaction)

        # Add funds from sale to user's account
        user.cash += (int(request.form.get("shares")) * quote["price"])

        # If selling all stock, delete from holdings
        if holding.shares == new_transaction.shares:
            db.session.delete(holding)

        # Otherwise, update the holding for the stock in the database
        else:
            holding.shares += new_transaction.shares # += because shares is negative due to sale

        # Save all changes to database
        db.session.commit()

        flash("Sale completed")
        return redirect("/portfolio")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        user = current_user
        stocks = user.holdings

        return render_template("sell.html", stocks=stocks)


@app.route("/sell/<string:symbol>")
@login_required
def sell_symbol(symbol):
    user = current_user
    stocks = user.holdings

    return render_template("sell.html", stocks=stocks, symbol=escape(symbol))


@app.route("/quote", methods=["POST"])
def quote():
    """Get stock quote via form submission"""

    # User reached route via POST (as by submitting a form via POST)
    symbol = request.form.get("symbol")

    # Validate length and alphabetical nature of symbol string
    if not (len(symbol) <= 5 and symbol.isalpha()):
        return render_template("index.html", error="Invalid symbol"), 400

    return redirect("/quote/" + symbol)


@app.route("/quote/<string:stock_symbol>")
def quote_symbol(stock_symbol):
    """Get stock quote"""

    # User reached route via GET (as by clicking a link or via redirect)
    # Get stock symbol from URL, escape user input to ensure safety
    symbol = escape(stock_symbol)

    # Validate length and alphabetical nature of symbol string
    if not (len(symbol) <= 5 and symbol.isalpha()):
        return render_template("index.html", error="Invalid symbol"), 400

    quote = lookup(symbol)

    if not quote:
        return render_template("index.html", error="Invalid symbol"), 400

    news_items = get_news(symbol)

    # Check if user is logged in, then check if they own the stock
    logged_in = False
    user_holding = None
    if not current_user.is_anonymous:
        logged_in = True
        user = current_user
        holding = Holding.query.filter((Holding.user_id == user.id) & (Holding.symbol == quote["symbol"])).first()

        if holding is not None:
            value = holding.shares * float(quote["price"])
            cost = 0

            # Calculate cost of all portfolio transactions
            # If sold stock, will subtract since shares in transaction will be negative
            transactions = Transaction.query.filter((Transaction.user_id == user.id) & (Transaction.symbol == quote["symbol"])).all()

            # Check if there are multiple transactions (have to check for single item when using filter)
            if type(transactions) is list:
                for transaction in transactions:
                    cost += transaction.shares * transaction.price
            # Otherwise, if transactions is not None, but not a list, must only be sinlge entry
            elif transactions:
                cost = transactions.shares * transactions.price

            user_holding = {
                "shares": holding.shares,
                "cost": cost,
                "value": value,
                "gain_loss": value - cost
            }

    return render_template("quote.html", quote=quote, news_items=news_items, logged_in=logged_in, user_holding=user_holding)


@app.route("/portfolio")
@login_required
def portfolio():
    """Show portfolio of user's stock holdings"""

    # Query database for current user's stock holdings (portfolio)
    user = current_user
    holdings = user.holdings
    stocks = [] # List of stock dicts
    transactions = user.transactions

    portfolio_cost = 0
    portfolio_value = 0

    # Get current prices for stocks using API
    for holding in holdings:
        quote = lookup(holding.symbol)
        stock = {}
        stock["symbol"] = holding.symbol
        stock["name"] = quote["name"]
        stock["price"] = float(quote["price"])
        stock["shares"] = int(holding.shares)
        stock["total_value"] = float(quote["price"]) * int(holding.shares)

        # Calculate cost of shares (total price paid)
        cost = 0
        for transaction in transactions:
            if transaction.symbol == stock["symbol"]:
                cost += transaction.shares * transaction.price # Sold shares will be negative

        stock["cost"] = cost / holding.shares
        stock["total_cost"] = cost
        stocks.append(stock) # Append stock dict to list of stocks
        portfolio_value += stock["total_value"]

    # Calculate cost of all portfolio transactions
    # Don't need to check for only single transaction since SQLAlchemy
    # with relationship returns InstrumentedList
    # If sold stock, will subtract since shares in transaction will be negative
    for transaction in transactions:
        portfolio_cost += transaction.shares * transaction.price

    # Format current user's portfolio info
    user_info = {
        "cash": user.cash,
        "portfolio_cost": portfolio_cost,
        "portfolio_value": portfolio_value,
        "gain_loss": portfolio_value - portfolio_cost
    }

    return render_template("portfolio.html", stocks=stocks, user_info=user_info)


@app.route("/history")
@login_required
def history():
    """Show history of user's transactions"""

    # Query database for all transactions made by current user
    user = current_user
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
        user = current_user

        if (user.cash >= 10000000):
            return render_template("addcash.html", error="Account already has too much cash ($10,000,000 or more)"), 400

        # Validate account won't end up with too much cash (> $10,000,000)
        if ((user.cash + int(request.form.get("cash"))) > 10000000):
            return render_template("addcash.html", error="Amount entered would lead the account to have too much cash ($10,000,000 or more). Please enter a lower amount."), 400

        user.cash += int(request.form.get("cash"))
        db.session.commit()

        flash("Cash amount added successfully")
        return redirect("/portfolio")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        user = current_user
        return render_template("addcash.html", cash=user.cash)


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
        if not (request.form.get("cash").isdigit() and int(request.form.get("cash")) >= 100 and int(request.form.get("cash")) <= 10000000):
            return render_template("register.html", error="Must provide valid starting cash amount (between $100 and $10,000,000)"), 400

        user = current_user

        user.cash = int(request.form.get("cash"))

        # Iterate through and delete user's holdings
        holdings = user.holdings
        for holding in holdings:
            db.session.delete(holding)

        # Iterate through and delete user's transactions
        transactions = user.transactions
        for transaction in transactions:
            db.session.delete(transaction)

        db.session.commit()

        flash("Account successfully reset")
        return redirect("/portfolio")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("reset.html")


# Processes errors
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("index.html", error=f"{e.name} - {e.code}")


# Listen for errors (like 404 not found)
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)