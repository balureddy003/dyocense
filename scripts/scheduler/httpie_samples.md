```bash
# Enqueue job
http POST :8000/queue/enqueue Authorization:"Bearer tenant_demo" \
  tenant_id=tenant_demo tier=pro \
  payload:='{"goaldsl":{"objective":{"cost":1.0}}}' \
  cost_estimate:='{"solver_sec":2.0}'

# Lease job as worker
http POST :8000/queue/lease Authorization:"Bearer worker_token" \
  worker_id=worker-1 max_jobs:=1

# Heartbeat
http POST :8000/queue/$JOB_ID/heartbeat Authorization:"Bearer worker_token" \
  worker_id=worker-1 lease_extension_seconds:=120

# Complete
http POST :8000/queue/$JOB_ID/complete Authorization:"Bearer worker_token" \
  worker_id=worker-1 result:='{"status":"done"}'
```
