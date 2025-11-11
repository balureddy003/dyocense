# Goals – Inline Wizard and Version History

This app now provides a friendlier flow from "no goals" to having multiple goals with lightweight versioning.

## First Goal: Inline AI Wizard

- When you have no goals, the page shows an inline wizard instead of a popup.
- Steps:
  1) Describe your goal in natural language
  2) AI structures it into a SMART, trackable goal (title, target, unit, deadline, category, auto-tracking)
  3) Review and Create
- You can cancel or Start Over at any time. The wizard also appears inline when you have only completed goals.

## Multiple Goals View

- Summary cards for Active/Completed/Auto‑Tracked and your streak
- Each goal card shows progress, days left, and connector source
- Quick actions:
  - Version badge (vN) – shows how many snapshots exist
  - History icon (✨) – opens a drawer with snapshots
  - Delete (🗑️)

## Version History (front‑end only)

- On create/update, we record a snapshot in `localStorage` under `goalVersions:<goalId>`.
- The history drawer orders snapshots newest‑first with timestamp, title, description, category, target/unit, deadline.
- This is provisional for UX; migrate to backend persistence when server versioning is available.

## Notes and Assumptions

- The AI structuring is mocked on the client today; replace with a backend call when ready.
- Versioning uses browser storage; clearing site data removes history.
- Server responses from create/update should include the whole Goal object for best snapshots.

## Dev Tips

```bash
# Build (from apps/smb)
npm run build
# Dev server
npm run dev
```
