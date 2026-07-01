#!/bin/sh
set -e

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Seeding chart of accounts, roles, and admin user..."
python manage.py bootstrap

exec "$@"
