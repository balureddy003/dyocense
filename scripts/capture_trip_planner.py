from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import argparse

START_URL = (
    "https://uk.trip.com/webapp/tripmap/tripplanner?source=t_online_homepage&locale=en-GB&curr=GBP"
)

# Heuristic selectors chosen to be resilient; may require tweaks if site updates.
SELECTORS = {
    "cookies_accept": "text=Accept all",
    "heading_to_button": "text=Heading to",
    "date_duration_button": "text=Date/Duration",
    "preferences_button": "text=Preferences",
    "ai_plan_cta": "text=Plan a Trip with AI",
    "preferences_confirm": "text=Confirm",
}

PREF_TOGGLES = [
    "text=Family",
    "text=Nature",
    "text=Relaxed",
    "text=Comfort",
]


def ensure_dir() -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    out_dir = Path("artifacts/runs/trip_planner_capture") / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def click_if_visible(page, selector: str, timeout: int = 3000):
    try:
        page.locator(selector).first.wait_for(state="visible", timeout=timeout)
        page.locator(selector).first.click()
        return True
    except PlaywrightTimeoutError:
        return False


def log_step(out_dir: Path, action: str, meta: dict | None = None):
    rec = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "meta": meta or {},
    }
    (out_dir / "steps.jsonl").write_text(
        ((out_dir / "steps.jsonl").read_text() if (out_dir / "steps.jsonl").exists() else "")
        + (str(rec) + "\n")
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Capture Trip.com planner flow")
    parser.add_argument("--origin", default="Fakenham", help="Origin city")
    parser.add_argument("--dest", action="append", default=["Paris"], help="Destination city (repeatable)")
    parser.add_argument("--headless", action="store_true", help="Run browser headless (default)")
    parser.add_argument("--headed", action="store_true", help="Run browser in headed mode")
    return parser.parse_args()


def main():
    args = parse_args()
    out_dir = ensure_dir()

    with sync_playwright() as p:
        headless = True if not args.headed else False
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(record_video_dir=str(out_dir / "video"))
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()

        page.goto(START_URL, wait_until="domcontentloaded")
        log_step(out_dir, "navigate", {"url": START_URL})
        # Handle cookies banner if present
        if click_if_visible(page, SELECTORS["cookies_accept"], timeout=5000):
            log_step(out_dir, "accept_cookies", {})

        # Try to add a destination
        if click_if_visible(page, SELECTORS["heading_to_button"], timeout=4000):
            # A text box should become focused; type a city and enter
            for d in args.dest:
                page.keyboard.type(d)
                page.keyboard.press("Enter")
                log_step(out_dir, "add_destination", {"value": d})
            time.sleep(1.0)
        else:
            # Try an alternative heuristic: search for an input near the text
            try:
                candidate = page.get_by_role("textbox").first
                candidate.click()
                for d in args.dest:
                    candidate.fill(d)
                    page.keyboard.press("Enter")
                    log_step(out_dir, "add_destination_alt", {"value": d})
                time.sleep(1.0)
            except Exception:
                pass

        # Open date/duration picker (best-effort)
        if click_if_visible(page, SELECTORS["date_duration_button"], timeout=2000):
            log_step(out_dir, "open_date_duration", {})
        time.sleep(0.5)
        page.keyboard.press("Escape")

        # Open preferences and toggle selections
        if click_if_visible(page, SELECTORS["preferences_button"], timeout=3000):
            log_step(out_dir, "open_preferences", {})
            for sel in PREF_TOGGLES:
                click_if_visible(page, sel, timeout=1000)
                log_step(out_dir, "toggle_pref", {"selector": sel})
            if click_if_visible(page, SELECTORS["preferences_confirm"], timeout=2000):
                log_step(out_dir, "confirm_preferences", {})

        # Trigger AI plan (if available)
        clicked_ai = click_if_visible(page, SELECTORS["ai_plan_cta"], timeout=3000)
        if clicked_ai:
            log_step(out_dir, "click_ai_plan", {})
            # Allow some time for the page to respond / render suggestions
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(2.0)

        # Capture artifacts
        page.screenshot(path=str(out_dir / "final_screenshot.png"), full_page=True)
        (out_dir / "final_html.html").write_text(page.content())
        log_step(out_dir, "capture_artifacts", {"files": ["final_screenshot.png", "final_html.html", "trace.zip"]})

        # Stop tracing and save
        trace_path = out_dir / "trace.zip"
        context.tracing.stop(path=str(trace_path))

        # Close
        context.close()
        browser.close()

    print(f"Capture complete. Artifacts in: {out_dir}")


if __name__ == "__main__":
    main()
