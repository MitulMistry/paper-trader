from flask import Flask

# Configure application
app = Flask(__name__)

@app.route("/")
def index():
    return "<p>Hello World! This is the Paper Trader app.</p>"