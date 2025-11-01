# alx_travel_app/settings.py

# ------------------ Celery Configuration ------------------
CELERY_BROKER_URL = 'amqp://localhost'  # RabbitMQ default URL
CELERY_RESULT_BACKEND = 'rpc://'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Nairobi'

# ------------------ Django Email Backend ------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'youremail@gmail.com'  # replace with env var in production
EMAIL_HOST_PASSWORD = 'yourpassword'     # use env var / app password
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
