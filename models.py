from app import db
from datetime import datetime

# Models used to translate into database schema using Flask-SQLAlchemy (ORM)
# User has many Holdings, and User has many Transactions (One-to-Many relationships)

class User(db.Model):
    # Set table name in database (override default)
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    cash = db.Column(db.Float, nullable=False, default=10000.00)
    holdings = db.relationship("Holding", backref="user", lazy=True)
    transactions = db.relationship("Transaction", backref="user", lazy=True)

    # Method to represent the object when we query for it
    def __repr__(self):
        return "<User %r>" % self.username

class Holding(db.Model):
    __tablename__ = "holdings"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(5), nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable="False")

    def __repr__(self):
        return "<Holding %r>" % self.symbol

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(5), nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable="False")

    def __repr__(self):
        return "<Transaction %r>" % self.timestamp
