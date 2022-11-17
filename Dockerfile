FROM python:3.9.5-alpine
RUN apk update \
    && apk add libpq postgresql-dev \
    && apk add build-base
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app
CMD ["gunicorn", "-b", "0.0.0.0:8080", "--workers", "3", "app:app"]