# syntax=docker/dockerfile:1

# Base image tags are literal (not ARGs) so Dependabot can track and bump them.

# ---- Build stage: resolve and install dependencies into an isolated venv ----
FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# ---- Runtime stage: minimal image, non-root user, read-only friendly ----
FROM python:3.13-slim AS runtime

ARG APP_VERSION=dev
ARG GIT_SHA=local

LABEL org.opencontainers.image.title="hello-spock" \
      org.opencontainers.image.description="A Django web app that greets Spock." \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${GIT_SHA}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    DJANGO_SETTINGS_MODULE=hello_spock.settings \
    APP_VERSION=${APP_VERSION} \
    GIT_SHA=${GIT_SHA} \
    PORT=8000

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY manage.py gunicorn.conf.py ./
COPY hello_spock ./hello_spock
COPY greeting ./greeting

# Static files are collected at build time; the key is a throwaway build-only value.
RUN DJANGO_SECRET_KEY=collectstatic-build-only python manage.py collectstatic --noinput

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]

CMD ["gunicorn", "hello_spock.wsgi:application"]
