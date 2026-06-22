#!/bin/bash
set -e

python manage.py migrate --noinput
python manage.py seed_iso25010
python manage.py collectstatic --noinput --clear

exec "$@"
