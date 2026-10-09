#!/usr/bin/env bash
# Generate API traffic to populate Grafana panels and push backend CPU up for the HPA demo.
#   URL=http://<ingress-host> CONCURRENCY=20 REQUESTS=3000 ./scripts/load-test.sh
# In another terminal:  kubectl get hpa -n helpdesk -w
set -euo pipefail
URL="${URL:-http://localhost:3000}"
CONCURRENCY="${CONCURRENCY:-20}"
REQUESTS="${REQUESTS:-3000}"

echo "Sending $REQUESTS requests to $URL with concurrency $CONCURRENCY..."
seq 1 "$REQUESTS" | xargs -P "$CONCURRENCY" -I{} sh -c '
  case $(( {} % 4 )) in
    0) curl -s -o /dev/null "$0/api/tickets" ;;
    1) curl -s -o /dev/null "$0/api/tickets/stats" ;;
    2) curl -s -o /dev/null "$0/api/tickets?q=checkout" ;;
    3) curl -s -o /dev/null "$0/api/tickets/999999" ;;   # deliberate 404s for the error-rate panel
  esac' "$URL"
echo "Load test completed"
