#!/bin/sh
set -e

echo "Applying migrations..."
python manage.py migrate --noinput
echo "Seeding chart of accounts and roles..."
python manage.py seed_coa
python manage.py seed_roles
python manage.py collectstatic --noinput || true

exec "$@"
