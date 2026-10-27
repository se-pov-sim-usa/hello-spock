"""ASGI entrypoint, for running under an ASGI server if ever needed."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hello_spock.settings")

application = get_asgi_application()
