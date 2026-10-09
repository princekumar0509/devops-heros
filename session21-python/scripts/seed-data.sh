#!/usr/bin/env bash
# Seed a handful of realistic tickets for demos.
#   ./scripts/seed-data.sh                       # local Compose (http://localhost:3000)
#   URL=http://<ingress-host> ./scripts/seed-data.sh
set -euo pipefail
URL="${URL:-http://localhost:3000}"

post() { curl -fsS -X POST "$URL/api/tickets$1" -H 'Content-Type: application/json' -d "$2"; }

id_of() { python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])'; }

t1=$(post "" '{"subject":"Checkout page returns HTTP 500","description":"Customers on mobile Safari get a 500 after entering card details.","category":"BUG","priority":"URGENT","requester_name":"Meera Iyer","requester_email":"meera@shopfast.in","agent":"Ravi Kumar"}' | id_of)
t2=$(post "" '{"subject":"Charged twice for October invoice","description":"Invoice INV-10293 shows two identical charges on my card.","category":"BILLING","priority":"HIGH","requester_name":"Arjun Mehta","requester_email":"arjun@acme.co"}' | id_of)
t3=$(post "" '{"subject":"Password reset email never arrives","description":"Tried three times, checked spam folder.","category":"ACCOUNT","priority":"MEDIUM","requester_name":"Asha Verma","requester_email":"asha@example.com","agent":"Neha Shah"}' | id_of)
post "" '{"subject":"Please add dark mode","description":"Would love a dark theme for late-night shifts.","category":"FEATURE_REQUEST","priority":"LOW","requester_name":"Kabir Singh","requester_email":"kabir@studio.io"}' >/dev/null
post "" '{"subject":"How do I export my data?","category":"GENERAL","priority":"LOW","requester_name":"Lena Fischer","requester_email":"lena@example.de"}' >/dev/null

post "/$t1/comments" '{"author":"Ravi Kumar","body":"Reproduced on iOS 18. Rolling back the payment SDK now."}' >/dev/null
post "/$t1/comments" '{"author":"Ravi Kumar","body":"Root cause: SDK 4.2 drops the CSRF header. Escalated to payments team.","internal":true}' >/dev/null
post "/$t2/comments" '{"author":"Arjun Mehta","body":"Attaching my bank statement screenshot."}' >/dev/null
curl -fsS -X PUT "$URL/api/tickets/$t3" -H 'Content-Type: application/json' -d '{"status":"RESOLVED"}' >/dev/null

echo "Seeded tickets into $URL"
curl -fsS "$URL/api/tickets/stats"; echo
