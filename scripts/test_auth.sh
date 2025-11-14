#!/bin/bash
# Quick auth test script

# Get token
TOKEN=$(curl -s -X POST http://127.0.0.1:8001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email": "admin@acme.com", "password": "password123", "tenant_id": "8278e5e6-574b-429f-9f65-2c25fa776ee9"}' \
  | jq -r '.access_token')

echo "Token: ${TOKEN:0:50}..."

# Test users endpoint
echo -e "\n=== Testing /api/v1/users/ ==="
curl -s -X GET "http://127.0.0.1:8001/api/v1/users/" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
