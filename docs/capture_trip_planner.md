# Trip.com Planner – Live Flow Capture

This guide shows how to record the Trip.com Trip.Planner flow (video, screenshots, and a Playwright trace) so we can replicate the UX in Dyocense.

Artifacts are stored under `artifacts/runs/trip_planner_capture/<timestamp>/`.

## One-time setup

```bash
make setup          # create venv and install dev deps (includes Playwright)
make setup-browsers # download Playwright browsers
```

## Record a session

Run the recorder (headless by default):

```bash
make capture-trip-planner
```

Pass custom inputs and watch the browser:

```bash
make capture-trip-planner ARGS="--headed --origin Fakenham --dest Paris --dest Rome"
```

Outputs in the timestamped directory:

- `final_screenshot.png` – full-page screenshot of the end state
- `final_html.html` – page HTML snapshot
- `trace.zip` – Playwright trace (open at <https://trace.playwright.dev>)
- `video/*.webm` – short recording of the session
- `steps.jsonl` – step-by-step action log (timestamped)

## Notes

- Selectors are text-based (e.g., “Heading to”, “Preferences”). If Trip.com updates labels, we’ll tweak selectors in `scripts/capture_trip_planner.py`.
- This is strictly for workflow analysis. Do not log personal data; purge artifacts if they contain sensitive info.

## Next

- Use the captured steps and the spec in `docs/trip_planner_flow.md` to implement the equivalent flow in Dyocense’s `apps/ui`.
- API contract and schemas: `docs/openapi/trip_planner.yaml`, `docs/schemas/trip_planner.schema.json`.
