# 🖖 hello-spock

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)
[![CodeQL](../../actions/workflows/codeql.yml/badge.svg)](../../actions/workflows/codeql.yml)

A small Django app that says **Hello, Spock**: a warp-speed starfield, a glass card and an LCARS accent bar. The app is deliberately tiny. The point of this repository is Continuous Integration: every change is linted, tested, scanned, built into a `linux/amd64` image and published to GitHub Packages, with Kubernetes manifests ready for Harness CD.

## Endpoints

| Path | Purpose |
|---|---|
| `/` | The greeting page; the footer shows the build version and commit |
| `/healthz` | Liveness probe (bypasses `ALLOWED_HOSTS` and the HTTPS redirect) |
| `/readyz` | Readiness probe |
| `/version` | JSON build info: version, commit, Python and Django versions |

## Local development

Requires Python 3.13+ and Docker.

```bash
make install
```

```bash
make run
```

Then open http://localhost:8000. Run `make help` to list every target. `make ci` runs the same checks as the pipeline: lint, security, tests, deploy checks and manifest validation (that last one needs `helm` and `kubeconform`).

### Configuration

All settings come from environment variables (see [.env.example](.env.example)):

| Variable | Default | Notes |
|---|---|---|
| `DJANGO_SECRET_KEY` | none | Required unless `DJANGO_DEBUG` is on |
| `DJANGO_DEBUG` | `false` | |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]` | Comma-separated |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | Comma-separated, with scheme |
| `DJANGO_SECURE_SSL_REDIRECT` | `true` in production | Set `false` when TLS terminates upstream |
| `DJANGO_SECURE_HSTS_SECONDS` | `31536000` in production | |
| `LOG_LEVEL` | `info` | |
| `GUNICORN_WORKERS` / `GUNICORN_THREADS` | `min(2×CPU+1, 4)` / `2` | |

## Continuous Integration

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on pull requests, pushes to `main`, `v*.*.*` tags and manual dispatch.

```
lint ─────────┐
test (3.13, 3.14) ─┤
security ─────┼──► docker: build ► smoke test ► Trivy ► push to GHCR ► attest
manifests ────┘
```

- **lint**: ruff (lint + format), hadolint for the Dockerfile, actionlint for the workflows.
- **test**: `manage.py check --deploy` against production settings, then pytest on a Python matrix with a 90% coverage gate. JUnit and coverage XML are uploaded as artifacts and a coverage table goes to the job summary.
- **security**: bandit static analysis and pip-audit against the runtime dependencies.
- **manifests**: renders [`deploy/k8s`](deploy/k8s) for the base values and each override, then validates the output with kubeconform (see [scripts/validate-manifests.sh](scripts/validate-manifests.sh)).
- **docker**: builds the `linux/amd64` image, runs it read-only and checks the endpoints and the non-root UID, then fails on fixable critical/high CVEs (Trivy, with the report sent to code scanning). Only after all that, and only for non-PR events, it pushes to `ghcr.io/<owner>/<repo>` with an SBOM and a signed build-provenance attestation.

Image tags:

| Event | Tags |
|---|---|
| Push to `main` | `main`, `sha-<short>`, `latest` |
| Tag `v1.2.3` | `1.2.3`, `1.2`, `sha-<short>` |
| Pull request | built and scanned, never pushed |

Other practices in the repo:

- **CodeQL** ([codeql.yml](.github/workflows/codeql.yml)) for Python and the workflows themselves, on PRs, `main` and weekly.
- **Dependabot** ([dependabot.yml](.github/dependabot.yml)) for pip, GitHub Actions and the Docker base image. Django stays on the 5.2 LTS line.
- **Actions pinned to commit SHAs**, with version comments that Dependabot keeps current.
- **Least-privilege tokens**: the workflow defaults to `contents: read`; only the docker job gets package and attestation write access.
- **pre-commit hooks** ([.pre-commit-config.yaml](.pre-commit-config.yaml)) mirror the lint job locally.

Verify a published image's provenance:

```bash
gh attestation verify oci://ghcr.io/<owner>/<repo>:latest --owner <owner>
```

### First-time GitHub setup

1. Create the repository and push `main`. The first CI run publishes the package.
2. Under **Settings → Code security**, enable code scanning so Trivy and CodeQL results show up.
3. Optionally protect `main` and require the `Lint`, `Test`, `Security`, `Kubernetes manifests` and `Docker image` checks.
4. The GHCR package starts out private. Either make it public, or give the Harness artifact connector credentials (see below).

## Kubernetes manifests for Harness CD

[`deploy/k8s`](deploy/k8s) uses Harness's native **K8s Manifest** format: Go-templated manifests in `templates/` plus a `values.yaml` full of Harness expressions.

| Value | Harness expression |
|---|---|
| `image` | `<+artifacts.primary.image>` |
| `dockercfg` | `<+artifacts.primary.imagePullSecret>` |
| `namespace` | `<+infra.namespace>` |
| `env.secrets.DJANGO_SECRET_KEY` | `<+secrets.getValue("hello_spock_django_secret_key")>` |

To use them in a Harness Kubernetes service:

1. **Manifest**: type *K8s Manifest*, pointing at `deploy/k8s/templates` in this repo, with values file `deploy/k8s/values.yaml`.
2. **Artifact**: a GitHub Package Registry (or Docker registry) source for `ghcr.io/<owner>/<repo>`. Use the `sha-<short>` or semver tags for traceable releases.
3. **Secret**: create a Harness secret with identifier `hello_spock_django_secret_key`.
4. **Overrides**: attach [`overrides/values-dev.yaml`](deploy/k8s/overrides/values-dev.yaml) or [`overrides/values-prod.yaml`](deploy/k8s/overrides/values-prod.yaml) as environment values overrides. Set the real hostname in the prod override first.

The templates work with Rolling, Canary and Blue Green. For Blue Green, set `blueGreen.enabled: true` to render the primary and stage services Harness swaps between. The workload runs as UID 10001 with a read-only root filesystem, no privilege escalation, all capabilities dropped and the `RuntimeDefault` seccomp profile.

No Harness pipelines are defined in this repository.
