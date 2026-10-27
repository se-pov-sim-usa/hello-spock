#!/usr/bin/env bash
# Render the Harness K8s manifests and validate them against Kubernetes schemas.
#
# Harness renders deploy/k8s/templates with Go templating (+ Sprig) against
# values.yaml, after resolving <+...> expressions. Helm uses the same template
# engine, so wrapping the folder in a throwaway chart gives a faithful render.
# Harness expressions are replaced with representative values for validation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFESTS="${ROOT}/deploy/k8s"
K8S_VERSION="${K8S_VERSION:-1.30.0}"
OUT_DIR="${OUT_DIR:-${ROOT}/.rendered}"

command -v helm >/dev/null || { echo "helm is required" >&2; exit 1; }
command -v kubeconform >/dev/null || { echo "kubeconform is required" >&2; exit 1; }

CHART="$(mktemp -d)"
trap 'rm -rf "${CHART}"' EXIT

cat >"${CHART}/Chart.yaml" <<'EOF'
apiVersion: v2
name: harness-render
version: 0.0.0
EOF
cp -R "${MANIFESTS}/templates" "${CHART}/templates"
cp "${MANIFESTS}/values.yaml" "${CHART}/values.yaml"

# Stand-ins for what Harness resolves at deploy time.
HARNESS_STANDINS=(
  --set-string namespace=hello-spock
  --set-string image=ghcr.io/example/hello-spock:sha-0000000
  --set-string dockercfg=eyJhdXRocyI6e319
  --set-string env.secrets.DJANGO_SECRET_KEY=validation-only-secret
)

mkdir -p "${OUT_DIR}"
status=0
for overrides in "" "${MANIFESTS}"/overrides/*.yaml; do
  label="$(basename "${overrides:-base}" .yaml)"
  args=()
  [[ -n "${overrides}" ]] && args=(--values "${overrides}")

  echo "==> Rendering ${label}"
  helm template hello-spock "${CHART}" "${args[@]+"${args[@]}"}" "${HARNESS_STANDINS[@]}" \
    >"${OUT_DIR}/${label}.yaml"

  if grep -n '<+' "${OUT_DIR}/${label}.yaml"; then
    echo "Unresolved Harness expression in rendered ${label} manifests" >&2
    status=1
  fi

  echo "==> Validating ${label} against Kubernetes ${K8S_VERSION}"
  kubeconform -strict -summary -kubernetes-version "${K8S_VERSION}" "${OUT_DIR}/${label}.yaml" || status=1
done

exit "${status}"
