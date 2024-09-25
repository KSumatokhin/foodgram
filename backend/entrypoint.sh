python manage.py makemigrations --no-input
python manage.py migrate --no-input
gunicorn --bind 0.0.0.0:8000 foodgram_backend.wsgi