# Trip Planner – Live Flow Capture and Implementation Spec

This document captures the UX flow of Trip.com’s Trip.Planner (referenced page and screenshot) and translates it into an actionable spec for our implementation.

Last updated: 2025-11-05

---

## Overview

Primary journey supported by the planner:

- Select origin (“Starting from …”), destination(s) (“Heading to …”), and date/duration.
- Optionally set preferences (with whom, travel style, pace, accommodation, and free-form needs).
- Trigger either “Create It Myself” (manual builder) or “Plan a Trip with AI”.
- Review generated itinerary, refine via filters/AI chat, save, and optionally book.

Key top controls mirrored from the live page:

- Starting from: single origin place (city/town).
- Heading to: one or more destinations (chips) with remove/reorder.
- Date/Duration: either specific dates or flexible duration.
- Preferences: modal with categories (see below).
- Primary CTAs: Create It Myself, Plan a Trip with AI.
- Secondary: My Itineraries (requires sign-in).

---

## Preferences Modal (as observed)

- With Whom: solo, family, couple, friends, elderly
- Travel Style: cultural, classic, nature, cityscape, historical
- Travel Pace: ambitious, relaxed
- Accommodation: comfort, premium, luxury
- Other Needs: free-text (0–1000 chars)

We also support optional constraints: wheelchair_access, visa_free_only, dietary_notes.

---

## State Machine (textual)

States

1. Start (idle)
2. InputsReady (origin + >=1 destination + date/duration)
3. Planning (request sent)
4. PlanReady (itinerary rendered)
5. Refining (user modifies preferences or uses AI refine)
6. Saved (persisted to account)
7. Booking (deep links to providers)

Transitions

- Start → InputsReady: user fills required fields
- InputsReady → Planning: clicks “Plan a Trip with AI” or “Create It Myself”
- Planning → PlanReady: receive TripPlan
- PlanReady ↔ Refining: chat/filters/drag re-order; produces PlanDelta → replan
- PlanReady → Saved: user saves itinerary (auth required)
- PlanReady → Booking: user books flights/hotels/activities (external links)

Error Modes

- Validation error (missing fields, invalid dates)
- No results (destinations unsupported/closed)
- Rate limit or transient error → show retry with backoff

---

## Contracts (high-level)

Inputs (TripRequest)

- origin: PlaceRef { id, name, type: city }
- destinations: PlaceRef[] (order matters)
- travel_window: either { start_date, end_date } or { duration_days }
- party: { adults, children, seniors, with_whom }
- preferences: { styles[], pace, accommodation, budget_total?, currency, other_needs? }
- constraints?: { wheelchair_access?, visa_free_only?, dietary_notes? }

Outputs (TripPlan)

- id, summary, currency, total_estimated_cost
- days[]: { date, city, activities[] }
- activities[]: { id, title, category, time_window, location, cost?, booking }
- travel_legs[]: inter-city transport suggestions
- lodging[]: nightly suggestions with price bands
- warnings[]: strings

Refinements (PlanDelta)

- add/remove/reorder destinations
- change duration or specific dates
- adjust pace/styles/accommodation/budget
- lock activities/lodging and replan around them

Detailed JSON Schema is in `docs/schemas/trip_planner.schema.json`.

---

## API Surface (OpenAPI stub)

Endpoints to implement (spec in `docs/openapi/trip_planner.yaml`):

- GET /places/suggest?query=…
- POST /trips/plan (TripRequest → TripPlan)
- GET /trips/{id}
- POST /trips/{id}/refine (PlanDelta → TripPlan)
- POST /trips/{id}/save
- POST /trips/{id}/book (stub; returns deep links)

---

## UI Implementation Notes

- Header form: inputs with validation and clear affordances for multiple destinations; destination chips with delete and drag handles.
- Preferences modal: grouped sections; persist selections between sessions.
- CTA behavior:
  - Create It Myself → open blank builder with selected skeleton (dates, cities).
  - Plan a Trip with AI → call /trips/plan; show skeleton loading cards.
- Plan screen: day-by-day itinerary with map pins; edit affordances.
- Refinement: left-side filters + AI chat. Chat proposes pending actions (PlanDelta) with explicit Apply.
- Auth gating: “My Itineraries” requires sign-in; otherwise prompt.

Accessibility & i18n

- All interactive elements keyboard navigable; ARIA labels.
- Copy and currency/units localized based on locale/curr.

---

## Edge Cases

- Duration < 1 day or > 60 days → validation error.
- > 8 destinations → suggest splitting into multiple trips.
- Start_date after end_date → error.
- Budget below minimum feasibility → warn and offer budget-agnostic plan.
- Elderly + Ambitious pace → warn and default to Relaxed unless confirmed.

---

## Non-Functional Requirements

- P95 plan generation < 5s (with cached place data)
- Offline-safe drafts in localStorage until saved
- Observability: log each PlanDelta and final Plan
- Privacy: do not store free-text needs unless user saves trip

---

## Mapping to Repository

- Frontend: `apps/ui` (new page: TripPlanner)
- APIs: add under `services/` (planner service or extend kernel gateway)
- Schemas: `docs/schemas/trip_planner.schema.json`
- OpenAPI: `docs/openapi/trip_planner.yaml`
