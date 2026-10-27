import pytest


@pytest.mark.parametrize(("path", "status"), [("/healthz", "alive"), ("/readyz", "ready")])
def test_probe_returns_status(client, path, status):
    response = client.get(path)

    assert response.status_code == 200
    assert response.json() == {"status": status}


@pytest.mark.parametrize("path", ["/healthz", "/readyz"])
def test_probe_ignores_allowed_hosts(client, path):
    # Kubelet probes use the pod IP as Host, which is never in ALLOWED_HOSTS.
    response = client.get(path, HTTP_HOST="10.42.0.17:8000")

    assert response.status_code == 200


@pytest.mark.parametrize("path", ["/healthz", "/readyz"])
def test_probe_is_not_redirected_to_https(client, settings, path):
    settings.SECURE_SSL_REDIRECT = True

    response = client.get(path)

    assert response.status_code == 200


def test_probe_supports_head(client):
    assert client.head("/healthz").status_code == 200


def test_regular_pages_still_enforce_allowed_hosts(client):
    response = client.get("/", HTTP_HOST="evil.example.com")

    assert response.status_code == 400


def test_probe_rejects_post(client):
    # Falls through to URL routing, which has no /healthz view.
    assert client.post("/healthz").status_code == 404
