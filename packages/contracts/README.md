# Contracts Package

This package owns the machine-readable contracts that define Dyocense interactions (OPS, SolutionPack, diagnostics, etc.). Schemas in `schemas/` are the single source of truth and fuel code generation, validation, and SDKs.

## Validation

Use the root `make validate` command (or run `python scripts/validate_ops.py`) to validate example payloads against the OPS schema. As additional schemas are introduced, extend the script and add new make targets.
