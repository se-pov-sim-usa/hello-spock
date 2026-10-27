import platform

import django
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe


@require_safe
def index(request):
    return render(request, "greeting/index.html", {"name": "Spock"})


@require_safe
def version(request):
    return JsonResponse(
        {
            "version": settings.APP_VERSION,
            "commit": settings.GIT_SHA,
            "python": platform.python_version(),
            "django": django.get_version(),
        }
    )
