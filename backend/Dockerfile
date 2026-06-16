FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static at build time (dummy settings values; no DB needed).
RUN SECRET_KEY=build DEBUG=False ALLOWED_HOSTS="*" python manage.py collectstatic --noinput

EXPOSE 8000

# On start: apply migrations, seed (idempotent), then serve. Shell form expands $PORT.
CMD python manage.py migrate --noinput && \
    python manage.py bootstrap && \
    gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3
