import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

from datetime import datetime, timedelta


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Make IEX API request
    try:
        api_key = os.getenv("IEX_API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"],
            "change": float(quote["change"]),
            "change_percent": float(quote["changePercent"])
        }
    except (KeyError, TypeError, ValueError):
        return None

def get_news(query, days=7, count=4):
    """Get news articles based on query."""

    # Make News API request
    try:
        api_key = os.getenv("NEWS_API_KEY")
        date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        url = f"https://newsapi.org/v2/everything?q={urllib.parse.quote_plus(query)}&from={date}&sortBy=popularity&apiKey={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        response1 = response.json()
        response2 = response1["articles"]
        response3 = response2[:count] # Slice fisrt N elements of list 
        articles = []
        for item in response3:
            # News API gives date and time: 2021-06-12T00:05:00Z
            date = item["publishedAt"].replace("T", " ").replace("Z", "")

            article = {
                "source": item["source"]["name"],
                "title": item["title"],
                "description": item["description"],
                "url": item["url"],
                "url_to_image": item["urlToImage"],
                "date": datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            }          
            articles.append(article)

        return articles
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
