# Decision Kernel Dashboard (Stub)

Single-page dashboard that shows orchestrated runs and evidence records, with the ability to trigger sample runs.

## Run

```bash
python -m http.server 4200 --directory apps/dashboard
```

Configure base URL/token via `config.js` (defaults to `http://localhost:8001` and `demo-tenant`).
