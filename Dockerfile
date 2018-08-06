FROM python:3.6

ENV FLASK_APP app.py

COPY globewriter.py gunicorn.py requirements.txt ./
COPY app app
COPY migrations migrations

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["gunicorn", "--config", "gunicorn.py", "app:app"]