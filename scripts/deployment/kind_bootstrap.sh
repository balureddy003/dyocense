#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME=${CLUSTER_NAME:-dyocense-dev}

if ! command -v kind >/dev/null 2>&1; then
  echo "kind not installed. Install from https://kind.sigs.k8s.io/docs/user/quick-start/" >&2
  exit 1
fi

if ! kind get clusters | grep -q "${CLUSTER_NAME}"; then
  echo "[kind] creating cluster ${CLUSTER_NAME}" >&2
  cat <<YAML | kind create cluster --name "${CLUSTER_NAME}" --config -
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
YAML
else
  echo "[kind] cluster ${CLUSTER_NAME} already exists" >&2
fi

echo "[kubectl] applying Dyocense base manifests" >&2
kubectl apply -k infra/k8s/base

echo "All components scheduled. Inspect with: kubectl get pods -n dyocense" >&2
