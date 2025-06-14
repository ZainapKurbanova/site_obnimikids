release: python sync_media_to_static.py && python manage.py collectstatic --noinput
web: gunicorn obnimikids.wsgi:application --log-file -
worker: python manage.py runbot
