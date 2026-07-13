FROM python:3.12-slim

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir -r /app/webapp/requirements-web.txt

WORKDIR /app/webapp

EXPOSE $PORT

CMD gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
