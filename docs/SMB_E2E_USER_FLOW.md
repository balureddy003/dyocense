# SMB end-to-end user flow (show value fast)

This blueprint defines the best-practice journey for SMB users to reach value in under 60–120 seconds, then deepen usage via repeatable automation.

## Personas and primary jobs-to-be-done

- Owner/GM: Understand performance, get weekly digest, catch anomalies.
- Ops/Store manager: Fix issues today; monitor KPIs; quick exports.
- Analyst-lite (often part-time): Build a simple forecast; share insights.

## Lifecycle phases

1) Discover → 2) Onboard → 3) Data intake → 4) Validate & map → 5) First insights → 6) Take action → 7) Automate → 8) Retain/expand

---

## 1) Discover

- Entry points: website, partner app, marketplace, shared link.
- Promise: “Upload a file or try our sample to see your top sales insights in under a minute.”
- CTA variants: Try sample data, Analyze my data, Forecast next month.

Success criteria

- CTR to onboarding > 40%.

---

## 2) Onboard (frictionless)

- Sign in: Google/Microsoft/Email. Defer business details until after first insight.
- Consent: minimal, clearly stating data use; link to policy.

Success criteria

- New user completes onboarding in < 20s.

---

## 3) Data intake (multiple friendly options)

Show four equal options with short help text and icons:

- Upload CSV/XLSX (template link; max size; supported formats).
- Link Google Sheet (read-only scope; sample Sheet link).
- Paste a table (smart parse; 10-row minimum recommended).
- Use sample dataset (zero-friction path).

Required columns (configurable):

- Date, Amount, Product. Optional: Quantity, Category, Region, Channel, Cost.

Empty‑state copy

- "We’ll auto-detect your columns and let you remap before analysis."

Success criteria

- Start-to-upload completion rate > 70%.

---

## 4) Validate & map (trust and control)

- 10-row preview with detected types.
- Smart mapping chips: Date → invoice_date [change] • Amount → net_sales [change] • Product → sku [change].
- Fixers: date format selector, timezone, currency, thousands/decimal, null handling.
- Derived fields: Amount = price × quantity if missing; Category from product if provided.
- Warnings panel with one-click fixes; don’t block unless required columns unresolved.
- Stepper: Upload → Validate → Clean → Analyze → Results.

Success criteria

- 90%+ of files auto-map without user edits.

---

## 5) First insights (deliver value fast)

Render within 5–8 seconds for sample; 10–20s for typical SMB uploads.

- Insight cards (3–5):
  - Trend: revenue up/down vs prior period.
  - Seasonality: weekday/month patterns.
  - Top/Bottom products and categories.
  - Anomalies: sudden spikes/drops.
  - Cohorts or channels if present.
- Each card shows: key number, short rationale, confidence/coverage note.
- Provide an insight transcript for the chat agent to reference.

Next steps (quick actions)

- Ask a question; Forecast next month; Export CSV/PNG; Create weekly email; Add threshold alert.

Success criteria

- Time to first insight (TTFI): < 60s (sample), < 120s (upload).

---

## 6) Take action (bridge to operations)

- Forecast view: next 4–12 weeks with bands; drivers and assumptions.
- Inventory or staffing suggestions (if Quantity/Cost available): reorder points, potential stockouts.
- Playbooks: prebuilt prompts ("Find products with margin < 20% this week").
- Exports: CSV, PDF, image; share link with permissions.

Success criteria

- ≥ 30% sessions trigger at least one action after insights.

---

## 7) Automate (stickiness)

- Save mapping as template per workspace; auto-apply next time.
- Scheduled email digest (weekly) with top changes + anomaly highlights.
- Alerts: revenue dip > X%, product stockout risk, margin erosion.
- Data refresh connectors (Sheets, S3/Drive) with webhook/polling.

Success criteria

- 25% users enable at least one automation in week 1.

---

## 8) Retain & expand

- Personalize home: last insights, upcoming alerts, shortcuts.
- Recommendations: "Add cost data to unlock margin insights"; "Connect POS for auto-refresh".
- In-product NPS and "Was this helpful?" under each card.

Success criteria

- 7-day return rate, digest open rate, alert click-through.

---

## Conversation patterns (for the agent)

Rules of thumb

- Never open with a data demand; first show or promise value.
- Ask-Confirm-Act loop: state what you’ll do, do it, summarize results, offer next actions.
- Offer 1–2 clear choices per step; include a no-upload path (sample).

Sample scripts

- First touch: "Do you want quick insights or a forecast? You can try our sample or use your data."
- After upload: "I detected Date=invoice_date, Amount=net_sales, Product=sku. Want to review or analyze now?"
- After results: "Here are 3 takeaways. Want a weekly email or a forecast?"

Edge handling

- Sparse data (<200 rows or <30 days): warn and adapt insights; recommend next steps.
- Mixed currencies/timezones: prompt to normalize; remember selection.
- Missing required columns: propose derived alternatives or degrade gracefully.

---

## Instrumentation & KPIs

Key metrics

- Onboard completion time; Upload start→finish; Auto-map rate; TTFI; Action and Automation adoption; Error rate by cause.

Events to log

- flow.start, upload.started, schema.autodetected, schema.confirmed, analyze.started, analyze.completed, insight.viewed, action.clicked, automation.enabled, error.{type}.

---

## Security & trust cues

- Clear consent line under upload; link to policy.
- "We don’t store your data without your consent" toggle.
- PII detection → offer to ignore columns.

---

## Implementation cheat sheet (repo hints)

- apps/ui: add Sample Data button, Template download, SchemaMapper component, ProgressStepper, InsightCards.
- services/*: lightweight /analyze endpoint with schema inference, fast summaries; streaming progress messages.
- packages/agents: update system prompt to follow Ask-Confirm-Act and include mapping/validation tool use.
- tests/: add minimal e2e for upload→map→analyze→insight.

---

## Acceptance checklist (minimal viable flow)

- [ ] User reaches first insight from sample in <60s.
- [ ] Upload → preview/mapping → analyze works for standard CSV.
- [ ] At least 3 insight cards with plain-language explanations.
- [ ] Next actions visible: Ask a question, Forecast, Export, Save mapping.
- [ ] Basic metrics emitted for the steps above.
