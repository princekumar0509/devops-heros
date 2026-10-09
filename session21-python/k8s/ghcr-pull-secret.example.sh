#!/usr/bin/env bash
# Only needed if your GHCR packages are PRIVATE (simplest: make them public in GitHub → Packages → Settings).
# Creates a pull secret from a GitHub personal access token with the read:packages scope.
#   GHCR_USER=<github-user> GHCR_TOKEN=<pat> ./k8s/ghcr-pull-secret.example.sh
# then deploy with:  --set 'imagePullSecrets[0].name=ghcr-pull'
set -euo pipefail
kubectl create secret docker-registry ghcr-pull \
  --namespace helpdesk \
  --docker-server=ghcr.io \
  --docker-username="${GHCR_USER:?set GHCR_USER}" \
  --docker-password="${GHCR_TOKEN:?set GHCR_TOKEN}" \
  --dry-run=client -o yaml | kubectl apply -f -
