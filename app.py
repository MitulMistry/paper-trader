import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

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
    # iex_key = app.config.get("IEX_KEY")
    # google_news_key = app.config.get("GOOGLE_NEWS_KEY")
    return "<p>Hello World! This is the Paper Trader app.</p>"