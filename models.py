from app import db

class User(db.Model):
    # Set table name in database (override default)
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    cash = db.Column(db.Integer, nullable=False)

    # Method to represent the object when we query for it
    def __repr__(self):
        return "<User %r>" % self.username

class Holding(db.Model):
    __tablename__ = "holdings"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(6), nullable=False)
    shares = db.Column(db.Float, nullable=False)

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(6), nullable=False)
    shares = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
