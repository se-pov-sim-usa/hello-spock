"""WSGI entrypoint, served by gunicorn in the container."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hello_spock.settings")

application = get_wsgi_application()
