# Dyocense Marketplace (OCI Bundles)
Publish archetypes, solvers, connectors as OCI bundles.

## Manifest (`manifest.yaml`)
```yaml
name: inventory-optimizer
version: 1.0.0
type: archetype
inputs:
  - sales_csv
limits:
  max_items: 10000
policies:
  - uk.labour
entrypoint:
  module: archetypes.inventory.main
pricing:
  model: per_solve
  amount: 0.01
```

## Lifecycle
1) Build: `dyocense bundle build`  
2) Sign: cosign + SBOM (CycloneDX)  
3) Publish: `dyocense bundle push`  
4) Review & certify: “Dyocense Verified”
