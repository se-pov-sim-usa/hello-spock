import importlib

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command

import hello_spock.settings as base_settings


@pytest.fixture
def reload_settings(monkeypatch):
    """Re-import the base settings module under a patched environment."""

    def _reload(**env):
        for key in ("DJANGO_DEBUG", "DJANGO_SECRET_KEY", "DJANGO_ALLOWED_HOSTS"):
            monkeypatch.delenv(key, raising=False)
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        return importlib.reload(base_settings)

    yield _reload
    monkeypatch.undo()
    importlib.reload(base_settings)


def test_secret_key_is_required_in_production(reload_settings):
    with pytest.raises(ImproperlyConfigured):
        reload_settings(DJANGO_DEBUG="false")


def test_debug_mode_falls_back_to_dev_key(reload_settings):
    module = reload_settings(DJANGO_DEBUG="true")

    assert module.DEBUG is True
    assert module.SECRET_KEY == "insecure-dev-only-key"
    assert module.SESSION_COOKIE_SECURE is False


def test_production_defaults_are_hardened(reload_settings):
    module = reload_settings(DJANGO_SECRET_KEY="x" * 60)

    assert module.DEBUG is False
    assert module.SECURE_SSL_REDIRECT is True
    assert module.SECURE_HSTS_SECONDS == 31536000
    assert module.SESSION_COOKIE_SECURE is True
    assert module.CSRF_COOKIE_SECURE is True


def test_allowed_hosts_parsed_from_env(reload_settings):
    module = reload_settings(
        DJANGO_SECRET_KEY="x" * 60,
        DJANGO_ALLOWED_HOSTS=" spock.example.com, ,vulcan.example.com ",
    )

    assert module.ALLOWED_HOSTS == ["spock.example.com", "vulcan.example.com"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("1", True), ("true", True), ("YES", True), ("on", True), ("0", False), ("no", False), ("", False)],
)
def test_env_bool(monkeypatch, raw, expected):
    monkeypatch.setenv("SPOCK_FLAG", raw)

    assert base_settings.env_bool("SPOCK_FLAG") is expected


def test_env_bool_default(monkeypatch):
    monkeypatch.delenv("SPOCK_FLAG", raising=False)

    assert base_settings.env_bool("SPOCK_FLAG", default=True) is True


def test_deploy_checks_pass(settings):
    settings.SECURE_SSL_REDIRECT = True

    call_command("check", "--deploy", "--fail-level", "WARNING")
