type ServiceUrls = Partial<{
  compile: string;
  forecast: string;
  policy: string;
  optimise: string;
  diagnose: string;
  explain: string;
  evidence: string;
  orchestrator: string;
}>;

const DEFAULT_BASE_URL = "http://localhost:8001";
const DEFAULT_SERVICE_URLS: Required<ServiceUrls> = {
  compile: DEFAULT_BASE_URL,
  forecast: DEFAULT_BASE_URL,
  policy: DEFAULT_BASE_URL,
  optimise: DEFAULT_BASE_URL,
  diagnose: DEFAULT_BASE_URL,
  explain: DEFAULT_BASE_URL,
  evidence: DEFAULT_BASE_URL,
  orchestrator: DEFAULT_BASE_URL,
};

export interface DecisionResult {
  ops: unknown;
  forecasts: unknown;
  policy: unknown;
  solution: unknown;
  diagnostics: unknown;
  explanation: unknown;
  evidenceReceipt: unknown;
}

interface RequestOptions {
  body?: unknown;
  method?: "GET" | "POST";
  service: keyof typeof DEFAULT_SERVICE_URLS;
  path: string;
}

export interface DyocenseClientOptions {
  token: string;
  serviceUrls?: ServiceUrls;
  fetchImpl?: typeof fetch;
}

export class DyocenseClient {
  private readonly serviceUrls: Required<ServiceUrls>;
  private readonly token: string;
  private readonly fetchImpl: typeof fetch;

  constructor({ token, serviceUrls, fetchImpl }: DyocenseClientOptions) {
    this.token = token;
    this.serviceUrls = { ...DEFAULT_SERVICE_URLS, ...serviceUrls };
    this.fetchImpl = fetchImpl ?? fetch;
  }

  async runDecisionFlow({
    goal,
    tenantId = "sdk-tenant",
    projectId = "sdk-run",
    horizon = 2,
  }: {
    goal: string;
    tenantId?: string;
    projectId?: string;
    horizon?: number;
  }): Promise<DecisionResult> {
    const ops = await this.compile({ goal, tenantId, projectId });
    const forecasts = await this.forecast({ ops, horizon });
    const policy = await this.policy({ ops, tenantId });
    const solution = await this.optimise({ ops });
    const diagnostics = await this.diagnose({ ops, solution });
    const explanation = await this.explain({
      goal,
      solution,
      forecasts,
      policy,
      diagnostics,
    });
    const evidenceReceipt = await this.evidence({
      runId: (solution as any).metadata?.run_id ?? projectId,
      tenantId,
      ops,
      solution,
      explanation,
    });

    return { ops, forecasts, policy, solution, diagnostics, explanation, evidenceReceipt };
  }

  async compile({ goal, tenantId, projectId }: { goal: string; tenantId?: string; projectId?: string }) {
    const response = await this.request({
      service: "compile",
      path: "/v1/compile",
      body: { goal, tenant_id: tenantId ?? "sdk-tenant", project_id: projectId ?? "sdk-run" },
    });
    return (response as any).ops;
  }

  async forecast({ ops, horizon }: { ops: any; horizon?: number }) {
    const demand = ops?.parameters?.demand ?? {};
    const series = Object.entries(demand).map(([name, value]) => ({ name, values: [value] }));
    return this.request({
      service: "forecast",
      path: "/v1/forecast",
      body: { horizon: horizon ?? 2, series },
    });
  }

  async policy({ ops, tenantId }: { ops: any; tenantId?: string }) {
    const body: any = { ops };
    if (tenantId) body.tenant_id = tenantId;
    return this.request({
      service: "policy",
      path: "/v1/policy/evaluate",
      body,
    });
  }

  async optimise({ ops }: { ops: any }) {
    const response = await this.request({
      service: "optimise",
      path: "/v1/optimise",
      body: { ops },
    });
    return (response as any).solution;
  }

  async diagnose({ ops, solution }: { ops: any; solution: any }) {
    return this.request({
      service: "diagnose",
      path: "/v1/diagnose",
      body: { ops, solution },
    });
  }

  async explain({
    goal,
    solution,
    forecasts,
    policy,
    diagnostics,
  }: {
    goal: string;
    solution: any;
    forecasts: any;
    policy: any;
    diagnostics: any;
  }) {
    return this.request({
      service: "explain",
      path: "/v1/explain",
      body: {
        goal,
        solution,
        forecasts: forecasts?.forecasts ?? [],
        policy,
        diagnostics,
      },
    });
  }

  async evidence({
    runId,
    tenantId,
    ops,
    solution,
    explanation,
  }: {
    runId: string;
    tenantId: string;
    ops: any;
    solution: any;
    explanation: any;
  }) {
    return this.request({
      service: "evidence",
      path: "/v1/evidence/log",
      body: {
        run_id: runId,
        tenant_id: tenantId,
        ops,
        solution,
        explanation,
      },
    });
  }

  async submitRun({ goal, projectId, horizon = 2, series }: { goal: string; projectId?: string; horizon?: number; series?: any[] }) {
    return this.request({
      service: "orchestrator",
      path: "/v1/runs",
      body: { goal, project_id: projectId, horizon, series },
    });
  }

  async getRun(runId: string) {
    return this.request({
      service: "orchestrator",
      path: `/v1/runs/${runId}`,
      method: "GET",
    });
  }

  private async request({ service, path, body, method = "POST" }: RequestOptions): Promise<any> {
    const url = `${this.serviceUrls[service]}${path}`;
    const response = await this.fetchImpl(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.token}`,
      },
      body: method === "POST" ? JSON.stringify(body ?? {}) : undefined,
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Request to ${url} failed (${response.status}): ${text}`);
    }
    return response.json();
  }
}
