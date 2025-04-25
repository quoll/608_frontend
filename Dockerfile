FROM python:3.11-slim

WORKDIR /app

COPY flask/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flask/ .

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]

# Expose the port that the Flask app runs on
EXPOSE 5000

