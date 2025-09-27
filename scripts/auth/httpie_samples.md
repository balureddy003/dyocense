```bash
# Issue token for tenant/user (base64 encoded by API)
http POST :8000/auth/token username=alice password=secret tenant_id=tenant_demo

# Use returned access_token as bearer
TOKEN="$(http --ignore-stdin POST :8000/auth/token username=alice password=secret tenant_id=tenant_demo | jq -r .access_token)"
http GET :8000/auth/me Authorization:"Bearer $TOKEN"
```
