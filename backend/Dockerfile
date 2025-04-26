FROM python:3.11-slim
LABEL authors="Stepanov V.A."

COPY . /app/

WORKDIR /app

RUN pip install -r /app/requirements.txt
RUN pip install gunicorn==20.1.0 psycopg2-binary

CMD ["sh", "-c", "python manage.py migrate && python -Xutf8 manage.py loaddata test_data.json && python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@admin.com', 'Praktikum+123')\" && python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8000 foodgram_back.wsgi"]
