#!/usr/bin/env bash
set -euo pipefail
URL="${1:-$(aws cloudformation describe-stacks --stack-name shopeasy --query "Stacks[0].Outputs[?OutputKey=='AppUrl'].OutputValue" --output text)}"
echo "Products:"
curl -fsS "$URL/api/products" | python3 -m json.tool | head -60
echo
echo "Placing a demo order..."
ORDER=$(curl -fsS -X POST "$URL/api/checkout" -H 'Content-Type: application/json' \
  -d '{"customer_email":"demo@example.com","items":[{"product_id":"p-008","qty":2},{"product_id":"p-010","qty":1}]}')
echo "$ORDER" | python3 -m json.tool
ID=$(echo "$ORDER" | python3 -c 'import json,sys; print(json.load(sys.stdin)["order_id"])')
echo
echo "Fetching order $ID:"
curl -fsS "$URL/api/orders/$ID" | python3 -m json.tool
