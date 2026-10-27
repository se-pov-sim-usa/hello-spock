from django.conf import settings


def build_info(request):
    """Expose build metadata so every page can show which CI build is running."""
    return {
        "app_version": settings.APP_VERSION,
        "git_sha": settings.GIT_SHA,
        "git_sha_short": settings.GIT_SHA[:7],
    }
