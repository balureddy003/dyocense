# Infrastructure

Phase 4 introduces the first Kubernetes manifests for the Dyocense control/data plane. Key structure:

- `k8s/base/` — Kustomize base including namespace, MongoDB (StatefulSet), Keycloak, NATS, individual services, and the unified `kernel-api` deployment.
- `docker-compose/` — Local stack for Keycloak, MongoDB, NATS, the unified kernel, and orchestrator (`docker compose -f infra/docker-compose/docker-compose.yaml up --build`). Bring your own Ollama/OpenAI instance for explanations.
- Future overlays (e.g., `k8s/overlays/dev`, `k8s/overlays/prod`) will tailor replicas, autoscaling, and secrets per environment.

Apply the base to a cluster (kind/k3d/minikube) with:

```bash
kubectl apply -k infra/k8s/base
```

The manifests reference container images such as `ghcr.io/dyocense/*:dev`. Substitute or build your own before deploying. Secrets/configs here are development-only; replace them with secure values for shared environments.
