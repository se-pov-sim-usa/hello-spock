from django.http import JsonResponse

HEALTH_PATHS = {"/healthz": "alive", "/readyz": "ready"}


class HealthCheckMiddleware:
    """Answer liveness and readiness probes before any other middleware runs.

    Kubelet probes send the pod IP as the Host header, which ALLOWED_HOSTS
    would reject, and they speak plain HTTP, which SECURE_SSL_REDIRECT would
    redirect. Short-circuiting here keeps both settings strict for real traffic.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        status = HEALTH_PATHS.get(request.path_info)
        if status is not None and request.method in {"GET", "HEAD"}:
            return JsonResponse({"status": status})
        return self.get_response(request)
