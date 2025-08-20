web: gunicorn --config gunicorn.conf.py server.wsgi:application
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
