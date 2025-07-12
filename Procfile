release: python manage.py migrate --noinput && python manage.py collectstatic --no-input
web: gunicorn runtimeexceptions.wsgi
worker: python manage.py db_worker --settings=runtimeexceptions.settings.prod --noreload
