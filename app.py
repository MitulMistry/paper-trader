import os
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

# Configure application
app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
        # TODO

        return redirect("/portfolio")
    
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in and create session"""
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # TODO

        return redirect("/portfolio")
    
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out and clear session"""
    
    # TODO

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
def quote():
    """Get stock quote"""

    # TODO
    # Get stock symbol from URL
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