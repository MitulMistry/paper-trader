# Paper Trader
A paper trading web application to practice trading stocks, built with Flask.

## Install Instructions
The application depends on Python, which can be installed and managed a variety of ways. For this project, I used [pyenv](https://github.com/pyenv/pyenv) and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv), following [this guide](https://realpython.com/intro-to-pyenv/).

Once Python is installed, install [Flask](https://flask.palletsprojects.com/en/2.0.x/installation/) using the command: `pip install Flask`.

To run the application in development mode, configure Flask by entering the following commands in the application directory:

```
export FLASK_APP=app.py
export FLASK_ENV=development
```
Then run either `flask run` or `python -m flask run` to start the development server.

For production, the application uses [Gunicorn](https://gunicorn.org/) for the server as defined in the [Procfile](/Procfile) (for [Heroku](https://www.heroku.com/) deployment).