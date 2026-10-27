import django
import pytest
from django.urls import reverse


def test_index_greets_spock(client):
    response = client.get(reverse("greeting:index"))

    assert response.status_code == 200
    assert "greeting/index.html" in [t.name for t in response.templates]
    content = response.content.decode()
    assert "Hello," in content
    assert "Spock" in content
    assert "Live long and prosper." in content


def test_index_shows_build_metadata(client, settings):
    settings.APP_VERSION = "1.2.3"
    settings.GIT_SHA = "0123456789abcdef"

    content = client.get(reverse("greeting:index")).content.decode()

    assert "1.2.3 @" in content
    assert "0123456" in content
    assert "0123456789abcdef" in content


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_index_rejects_unsafe_methods(client, method):
    response = getattr(client, method)(reverse("greeting:index"))

    assert response.status_code == 405


def test_index_sends_security_headers(client):
    response = client.get(reverse("greeting:index"))

    assert response["X-Frame-Options"] == "DENY"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_index_redirects_http_to_https_when_enabled(client, settings):
    settings.SECURE_SSL_REDIRECT = True

    response = client.get(reverse("greeting:index"))

    assert response.status_code == 301
    assert response["Location"].startswith("https://")


def test_version_reports_build_info(client, settings):
    settings.APP_VERSION = "2.0.0"
    settings.GIT_SHA = "cafebabe"

    response = client.get(reverse("greeting:version"))

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "2.0.0"
    assert body["commit"] == "cafebabe"
    assert body["django"] == django.get_version()
    assert body["python"]
