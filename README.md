# Paper Trader
A paper trading web application to practice trading stocks, built with Flask.

## Install Instructions
The application depends on Python, which can be installed and managed a variety of ways. For this project, I used [pyenv](https://github.com/pyenv/pyenv) and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv), following [this guide](https://realpython.com/intro-to-pyenv/).

Once Python is installed, install [Flask](https://flask.palletsprojects.com/en/2.0.x/installation/) using the command: `pip install Flask`.

To run the application in development mode, configure Flask by entering the following commands in the application directory:

```
export FLASK_APP=app.py
export FLASK_ENV=development
export DATABASE_URL=""
export IEX_API_KEY=""
export NEWS_API_KEY=""
```
Insert the url for the Postgresql database in the quotes after DATABASE_URL. Insert the Google News and IEX API keys in their respective spots as well (after registering for accounts).

Then run either `flask run` or `python -m flask run` to start the development server.

For production, the application uses [Gunicorn](https://gunicorn.org/) for the server as defined in the [Procfile](/Procfile) (for [Heroku](https://www.heroku.com/) deployment).

## Project Structure
[`app.py`](/app.py) - Application logic.

[`config.py`](/conifg.py) - Configuration settings for different environments (development, production, etc.).

[`models.py`](/models.py) - Definitions for models using [SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/) as the ORM.

[`Procfile`](/Procfile) - Configuration for Heroku production deployment [Gunicorn](https://gunicorn.org/).

`.env` - Where you can store environment variables like FLASK_APP, FLASK_ENV, DATABASE_URL, IEX_KEY, GOOGLE_NEWS_KEY (Not commited to Git).