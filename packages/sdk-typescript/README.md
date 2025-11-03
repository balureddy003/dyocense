# Dyocense TypeScript SDK (Stub)

Early TypeScript wrapper around the Decision Kernel services. Designed for Node/Edge runtimes and browser usage via fetch.

## Install (local development)

```bash
npm install --save-dev typescript
npm install @dyocense/sdk --workspace packages/sdk-typescript
```

## Usage

```ts
import { DyocenseClient } from "@dyocense/sdk";

const client = new DyocenseClient({ token: "demo-tenant" });
const result = await client.runDecisionFlow({ goal: "Reduce holding cost" });
console.log(result.explanation.summary);

const run = await client.submitRun({ goal: "Reduce holding cost" });
const status = await client.getRun(run.run_id as string);
console.log(status.status);
```

The stub client defaults to the unified kernel endpoint (`http://localhost:8001`). Override `serviceUrls` if you need to target individual service ports or a remote gateway.
