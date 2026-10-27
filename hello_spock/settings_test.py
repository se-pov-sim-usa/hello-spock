"""Settings for the test suite: production settings with test-only overrides."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key-that-is-long-enough-for-check-deploy-0123456789")

from hello_spock.settings import *  # noqa: F403

# Tests talk plain HTTP through the test client; the redirect itself is covered explicitly.
SECURE_SSL_REDIRECT = False

# The manifest storage needs `collectstatic` to have run; tests don't need hashed files.
STORAGES = {"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
