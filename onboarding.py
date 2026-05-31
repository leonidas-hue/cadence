"""Onboarding test harness — orchestrates the diagnostic + week-1 audio generation
+ static HTML page for the user to actually do a week of the program.

Usage:
    python onboarding.py                    # full flow: diagnostic, generate audio, build HTML
    python onboarding.py --rebuild-html     # skip diagnostic + generation, just rebuild HTML
    python onboarding.py --reset            # delete saved diagnostic state and start over

After running, open onboarding.html in a browser.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

# Local imports — these live in the same directory as this script
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from routing import route, format_result  # noqa: E402
from audio.parser import parse_content_dir  # noqa: E402


STATE_DIR = ROOT / "state"
STATE_FILE = STATE_DIR / "diagnostic.json"
AUDIO_OUTPUT_DIR = ROOT / "audio_output" / "onboarding"
HTML_OUTPUT = ROOT / "onboarding.html"
QUESTIONS_PATH = ROOT / "questions.json"


# ────────────────────────────────────────────────────────────────────
# CLI rendering helpers (lifted from cli.py — kept self-contained here
# so onboarding.py is a single-entry-point harness)
# ────────────────────────────────────────────────────────────────────

def _hr(char: str = "─", width: int = 70) -> str:
    return char * width


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines, line = [], ""
    for w in words:
        if len(line) + len(w) + 1 > width:
            lines.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        lines.append(line)
    return lines


def _print_section_header(section: dict) -> None:
    print()
    print(_hr("═"))
    print(f"  {section['title']}")
    print(_hr("═"))
    if section.get("description"):
        print()
        for ln in _wrap(section["description"], 68):
            print(f"  {ln}")
    print()


def _ask_single_select(q: dict) -> object:
    print()
    for ln in _wrap(q["text"], 68):
        print(f"  {ln}")
    print()
    options = q["options"]
    for i, opt in enumerate(options, start=1):
        print(f"    {i}. {opt['label']}")
    print()
    while True:
        raw = input("  > ").strip()
        if not raw.isdigit():
            print("  Please enter a number.")
            continue
        idx = int(raw)
        if 1 <= idx <= len(options):
            return options[idx - 1]["value"]
        print(f"  Please enter a number between 1 and {len(options)}.")


def _ask_yes_no(q: dict) -> bool:
    print()
    for ln in _wrap(q["text"], 68):
        print(f"  {ln}")
    print()
    while True:
        raw = input("  (y/n) > ").strip().lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  Please answer y or n.")


def _ask(q: dict) -> object:
    if q["type"] == "single_select":
        return _ask_single_select(q)
    if q["type"] == "yes_no":
        return _ask_yes_no(q)
    raise ValueError(f"Unknown question type: {q['type']}")


# ────────────────────────────────────────────────────────────────────
# Diagnostic flow + state persistence
# ────────────────────────────────────────────────────────────────────

def run_diagnostic() -> dict:
    """Walks the user through the diagnostic and returns a state dict
    containing responses, routing result, and start date."""
    with open(QUESTIONS_PATH) as f:
        schema = json.load(f)

    print()
    print(_hr("═"))
    print("  CADENCE — Onboarding Test Harness")
    print(f"  Diagnostic Intake (v{schema['version']})")
    print(_hr("═"))
    print()
    print("  This intake takes 3-5 minutes and routes you to one of four")
    print("  evidence-based protocols. Your answers stay on this device.")
    print()
    print("  Press Enter to begin.")
    input()

    # Run only the diagnostic sections first
    diagnostic_sections = [
        s for s in schema["sections"] if not s.get("show_after_routing", False)
    ]
    preferences_sections = [
        s for s in schema["sections"] if s.get("show_after_routing", False)
    ]

    responses: dict[str, object] = {}
    for section in diagnostic_sections:
        _print_section_header(section)
        for q in section["questions"]:
            responses[q["id"]] = _ask(q)

    result = route(responses)
    variant = result["variant"]

    # Show the routing result before asking preferences
    print()
    print(format_result(result))
    print()

    # Now ask the preference questions, filtered by variant
    prefs: dict[str, object] = {}
    for section in preferences_sections:
        relevant = [
            q for q in section["questions"]
            if variant in q.get("applies_to_variants", [])
        ]
        if not relevant:
            continue
        _print_section_header(section)
        for q in relevant:
            prefs[q["id"]] = _ask(q)

    state = {
        "responses": responses,
        "result": result,
        "preferences": prefs,
        "start_date": dt.date.today().isoformat(),
        "voice_preference": "adam",  # default; toggleable in HTML
    }
    return state


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    print(f"  Saved state to {STATE_FILE.relative_to(ROOT)}")


def load_state() -> dict | None:
    if not STATE_FILE.exists():
        return None
    with open(STATE_FILE) as f:
        return json.load(f)


# ────────────────────────────────────────────────────────────────────
# Audio generation for the routed week-1
# ────────────────────────────────────────────────────────────────────

def collect_week1_jobs(variant_letter: str):
    """Returns the AudioJob list for the user's week 1 (both voices baked in
    at the generator level). Includes all branches if the variant branches
    in week 1 (Variant D Days 1 and 5)."""
    content_dir = ROOT / "content"
    all_jobs = parse_content_dir(content_dir)
    return [
        j for j in all_jobs
        if j.variant == variant_letter.lower() and j.week == 1
    ]


def generate_week1_audio(variant_letter: str, dry_run: bool = False) -> dict:
    from audio.generate import generate_jobs
    jobs = collect_week1_jobs(variant_letter)
    print(f"\n  Found {len(jobs)} session jobs for Variant {variant_letter.upper()} week 1.")
    if not jobs:
        print(f"  ⚠ No jobs found. Check that content/variant_{variant_letter.lower()}_week_1.md exists.")
        return {"generated": 0, "skipped": 0, "failed": 0}

    summary = generate_jobs(
        jobs,
        output_dir=AUDIO_OUTPUT_DIR,
        dry_run=dry_run,
    )
    return summary


def generate_library_audio(dry_run: bool = False) -> dict:
    """Generate audio for the 5 practice-library items (both voices).

    These are the breath patterns, mindfulness daily, and pre-session prep.
    They live in the same output_dir as variant audio but are prefixed with
    `library_` so they're visually distinct in the directory listing."""
    from audio.generate import generate_jobs
    from audio.library import parse_library

    library_jobs = parse_library()
    print(f"\n  Found {len(library_jobs)} practice library items.")
    summary = generate_jobs(
        library_jobs,
        output_dir=AUDIO_OUTPUT_DIR,
        dry_run=dry_run,
    )
    return summary


# ────────────────────────────────────────────────────────────────────
# HTML page generation
# ────────────────────────────────────────────────────────────────────

VARIANT_NAMES = {
    "A": "Anxiety-Driven Acquired",
    "B": "Hypertonic Pelvic Floor",
    "C": "Lifelong / Hypotonic",
    "D": "Porn-Conditioned / Masturbation-Pattern",
}

VARIANT_DESCRIPTIONS = {
    "A": "Anxiety regulation, breath, sensate focus, light pelvic floor maintenance.",
    "B": "Safety-critical. Reverse Kegels, diaphragmatic breath, hip mobility. No standard Kegels anywhere — they would worsen your profile.",
    "C": "Standard Kegel building, longer 8-12 week timeline. Pharma educational module in week 5.",
    "D": "Grip / pace / visual stimulus recalibration. Branches at week 4-5 depending on current or past porn use.",
}


def build_html(state: dict) -> str:
    """Builds the static HTML onboarding page. All audio paths are relative
    to the project root, so the HTML works when opened directly from the
    filesystem."""
    variant = state["result"]["variant"]
    variant_name = VARIANT_NAMES.get(variant, "Unknown")
    variant_desc = VARIANT_DESCRIPTIONS.get(variant, "")
    flags = state["result"].get("flags", [])
    reasoning = state["result"].get("reasoning", [])
    start_date = dt.date.fromisoformat(state["start_date"])
    today = dt.date.today()
    days_elapsed = (today - start_date).days
    current_day_idx = min(max(days_elapsed, 0), 6)  # clamp to 0-6 (days 1-7)

    jobs = collect_week1_jobs(variant)
    # Group jobs by day; within a day, jobs may have multiple branches
    jobs_by_day: dict[int, list] = {}
    for job in jobs:
        jobs_by_day.setdefault(job.day, []).append(job)

    days_html: list[str] = []
    for day in sorted(jobs_by_day.keys()):
        is_today = (day - 1) == current_day_idx
        is_past = (day - 1) < current_day_idx
        day_class = "today" if is_today else ("past" if is_past else "future")
        day_label = f"Day {day}"
        if is_today:
            day_label += " — today"
        elif is_past:
            day_label += " — already passed"

        sessions_html = []
        for job in jobs_by_day[day]:
            title = job.title
            branch_label = ""
            if job.branch:
                branch_label = f'<span class="branch">{job.branch}</span>'

            # Player blocks per voice
            adam_filename = job.audio_filename("adam")
            bella_filename = job.audio_filename("bella")
            adam_path = f"audio_output/onboarding/{adam_filename}"
            bella_path = f"audio_output/onboarding/{bella_filename}"

            sessions_html.append(f"""
                <div class="session">
                    <div class="session-title">{title} {branch_label}</div>
                    <div class="players">
                        <div class="player adam-player">
                            <label>Adam</label>
                            <audio controls preload="none" src="{adam_path}"></audio>
                        </div>
                        <div class="player bella-player">
                            <label>Bella</label>
                            <audio controls preload="none" src="{bella_path}"></audio>
                        </div>
                    </div>
                </div>
            """)

        sessions_block = "\n".join(sessions_html)
        days_html.append(f"""
            <div class="day {day_class}">
                <div class="day-header">{day_label}</div>
                {sessions_block}
            </div>
        """)

    days_block = "\n".join(days_html)

    # Practice Library block — always shown regardless of pacing tier.
    # Lists the standalone practice audio (breath patterns, mindfulness, pre-session prep)
    # with players. The user can launch any of them any time.
    from audio.library import parse_library
    library_jobs = parse_library()
    library_items_html: list[str] = []
    audio_output_subdir = AUDIO_OUTPUT_DIR.name  # "onboarding"
    for lj in library_jobs:
        adam_filename = lj.audio_filename("adam")
        bella_filename = lj.audio_filename("bella")
        adam_path = f"audio_output/{audio_output_subdir}/{adam_filename}"
        bella_path = f"audio_output/{audio_output_subdir}/{bella_filename}"
        # Check if audio actually exists; if not, show a placeholder
        adam_exists = (AUDIO_OUTPUT_DIR / adam_filename).exists()
        bella_exists = (AUDIO_OUTPUT_DIR / bella_filename).exists()

        if adam_exists or bella_exists:
            players = f"""
                    <div class="players">
                        <div class="player adam-player">
                            <label>Adam</label>
                            {'<audio controls preload="none" src="' + adam_path + '"></audio>' if adam_exists else '<div class="missing">not generated</div>'}
                        </div>
                        <div class="player bella-player">
                            <label>Bella</label>
                            {'<audio controls preload="none" src="' + bella_path + '"></audio>' if bella_exists else '<div class="missing">not generated</div>'}
                        </div>
                    </div>
            """
        else:
            players = '<div class="missing-both">Audio not yet generated. Run <code>python onboarding.py</code> without <code>--skip-library</code> to produce.</div>'

        library_items_html.append(f"""
            <div class="library-item">
                <div class="library-item-header">
                    <span class="library-item-title">{lj.title}</span>
                    <span class="library-item-duration">{lj.duration}</span>
                </div>
                <div class="library-item-use-case">{lj.use_case}</div>
                {players}
            </div>
        """)

    library_block = "\n".join(library_items_html)

    flags_html = ""
    if flags:
        flags_html = "<div class='flags'><strong>Flags:</strong> " + ", ".join(flags) + "</div>"

    reasoning_html = ""
    if reasoning:
        items = "".join(f"<li>{r}</li>" for r in reasoning)
        reasoning_html = f"<details><summary>Why this variant?</summary><ul>{items}</ul></details>"

    # Preferences block
    prefs = state.get("preferences", {})
    prefs_html = ""
    if prefs:
        speed = prefs.get("advancement_speed", "standard")
        time_tier = prefs.get("daily_time_commitment", "standard")
        speed_label = {
            "standard": "Standard (one core session per day, 8 weeks)",
            "extended": "Extended (every other day, ~16 weeks)",
        }.get(speed, speed)
        time_label = {
            "quick": "Quick (5-10 min)",
            "standard": "Standard (15-25 min)",
            "extended": "Extended (30-45 min)",
            "deep": "Deep (45-60 min)",
        }.get(time_tier, time_tier)

        addons_chosen = []
        if prefs.get("addon_mindfulness") == "yes":
            addons_chosen.append("Daily mindfulness")
        if prefs.get("addon_pelvic") == "yes":
            addons_chosen.append("Supplementary pelvic floor")
        if prefs.get("addon_breathwork") == "yes":
            addons_chosen.append("Extra breathwork")
        addons_str = ", ".join(addons_chosen) if addons_chosen else "none"

        # What the daily plan looks like at this tier
        tier_composition = {
            "quick": ["Today's core session only."],
            "standard": ["Core session + one daily add-on (mindfulness, breath, or PFM)."],
            "extended": [
                "Core session",
                "Add-ons you opted into",
                "Body scan from practice library (~10 min)",
                "One breath pattern (~5 min)",
            ],
            "deep": [
                "Core session",
                "Add-ons you opted into",
                "Body scan from practice library (~10 min)",
                "One breath pattern (~5 min)",
                "Daily reflection / journaling prompts (~10 min)",
                "Pre-session prep when relevant (~10 min)",
            ],
        }.get(time_tier, [])
        composition_html = "".join(f"<li>{item}</li>" for item in tier_composition)

        prefs_html = f"""
        <div class="prefs-card">
            <div class="prefs-row"><strong>Pacing:</strong> {speed_label}</div>
            <div class="prefs-row"><strong>Daily time:</strong> {time_label}</div>
            <div class="prefs-row"><strong>Add-ons:</strong> {addons_str}</div>
            <details>
                <summary>What your daily plan looks like</summary>
                <ul>{composition_html}</ul>
                <p style="font-size: 12px; color: #888; margin-top: 8px;">
                    Hard caps still apply regardless of tier: pelvic floor work won't exceed 15 min/day,
                    stop-start/edging stays at 2-3 sessions/week.
                </p>
            </details>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Cadence — Onboarding Test</title>
<style>
    * {{ box-sizing: border-box; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
        max-width: 760px;
        margin: 0 auto;
        padding: 32px 24px 80px;
        line-height: 1.55;
        color: #1c1c1c;
        background: #fafaf8;
    }}
    h1 {{
        font-size: 24px;
        margin: 0 0 4px;
        font-weight: 600;
    }}
    .subtitle {{
        color: #666;
        margin-bottom: 24px;
        font-size: 14px;
    }}
    .variant-card {{
        background: white;
        border: 1px solid #e0e0d8;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 32px;
    }}
    .prefs-card {{
        background: white;
        border: 1px solid #e0e0d8;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 32px;
        font-size: 14px;
    }}
    .prefs-row {{
        padding: 4px 0;
        color: #444;
    }}
    .prefs-row strong {{
        display: inline-block;
        min-width: 100px;
        color: #1c1c1c;
    }}
    .variant-letter {{
        display: inline-block;
        background: #1c1c1c;
        color: white;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 4px;
        margin-right: 8px;
    }}
    .variant-name {{
        font-size: 18px;
        font-weight: 600;
    }}
    .variant-desc {{
        margin-top: 12px;
        color: #444;
        font-size: 14px;
    }}
    .flags {{
        margin-top: 12px;
        font-size: 13px;
        color: #666;
    }}
    details {{
        margin-top: 12px;
        font-size: 13px;
        color: #666;
    }}
    summary {{
        cursor: pointer;
        font-weight: 500;
    }}
    details ul {{
        margin: 8px 0 0 0;
        padding-left: 18px;
    }}
    .pilot-note {{
        background: #fff8e1;
        border-left: 3px solid #f4b400;
        padding: 12px 16px;
        font-size: 13px;
        color: #5b4500;
        margin-bottom: 32px;
        border-radius: 0 4px 4px 0;
    }}
    .voice-pref {{
        margin-bottom: 24px;
        padding: 12px 16px;
        background: white;
        border: 1px solid #e0e0d8;
        border-radius: 6px;
        font-size: 14px;
    }}
    .voice-pref label {{
        margin-right: 16px;
        cursor: pointer;
    }}
    .day {{
        background: white;
        border: 1px solid #e0e0d8;
        border-radius: 8px;
        margin-bottom: 16px;
        padding: 16px 20px;
        transition: opacity 0.2s;
    }}
    .day.past {{ opacity: 0.55; }}
    .day.today {{ border-color: #1c1c1c; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
    .day.future {{}}
    .day-header {{
        font-weight: 600;
        font-size: 15px;
        margin-bottom: 12px;
        color: #1c1c1c;
    }}
    .day.today .day-header::after {{
        content: " ●";
        color: #d04a3a;
    }}
    .session {{
        margin-top: 14px;
        padding-top: 14px;
        border-top: 1px dashed #e8e8e2;
    }}
    .session:first-of-type {{
        margin-top: 0;
        padding-top: 0;
        border-top: none;
    }}
    .session-title {{
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 8px;
    }}
    .branch {{
        display: inline-block;
        font-size: 11px;
        text-transform: uppercase;
        background: #f0eee5;
        color: #555;
        padding: 1px 6px;
        border-radius: 3px;
        margin-left: 6px;
        vertical-align: 1px;
    }}
    .players {{
        display: flex;
        gap: 16px;
        flex-wrap: wrap;
    }}
    .player {{
        flex: 1;
        min-width: 280px;
    }}
    .player label {{
        display: block;
        font-size: 12px;
        color: #888;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    audio {{
        width: 100%;
        height: 36px;
    }}
    .hide-adam .adam-player {{ display: none; }}
    .hide-bella .bella-player {{ display: none; }}
    .hide-adam .player.bella-player,
    .hide-bella .player.adam-player {{
        flex: 1 1 100%;
    }}
    .library-heading {{
        margin: 48px 0 8px;
        font-size: 18px;
        font-weight: 600;
        color: #1c1c1c;
    }}
    .library-intro {{
        font-size: 13px;
        color: #666;
        margin-bottom: 20px;
        line-height: 1.5;
    }}
    .library-grid {{
        display: flex;
        flex-direction: column;
        gap: 12px;
    }}
    .library-item {{
        background: white;
        border: 1px solid #e0e0d8;
        border-radius: 8px;
        padding: 16px 20px;
    }}
    .library-item-header {{
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 4px;
    }}
    .library-item-title {{
        font-weight: 600;
        font-size: 14px;
    }}
    .library-item-duration {{
        font-size: 12px;
        color: #888;
    }}
    .library-item-use-case {{
        font-size: 13px;
        color: #555;
        margin-bottom: 10px;
        line-height: 1.5;
    }}
    .missing {{
        font-size: 12px;
        color: #b87a00;
        font-style: italic;
    }}
    .missing-both {{
        font-size: 13px;
        color: #b87a00;
        background: #fff8e1;
        padding: 8px 12px;
        border-radius: 4px;
    }}
    .missing-both code {{
        background: rgba(0,0,0,0.06);
        padding: 1px 5px;
        border-radius: 3px;
        font-size: 12px;
    }}
    footer {{
        margin-top: 48px;
        padding-top: 24px;
        border-top: 1px solid #e0e0d8;
        font-size: 12px;
        color: #888;
    }}
</style>
</head>
<body class="">

<h1>Cadence — Week 1</h1>
<div class="subtitle">Onboarding test • Generated {today.isoformat()}</div>

<div class="pilot-note">
    <strong>Note on this audio.</strong> These files are unrefined pilot output.
    You'll hear pacing issues, occasional cut-off words, and weird pauses — those
    are known and on the fix list. Listen for protocol fit and tone direction,
    not surface polish.
</div>

<div class="variant-card">
    <span class="variant-letter">{variant}</span><span class="variant-name">{variant_name}</span>
    <div class="variant-desc">{variant_desc}</div>
    {flags_html}
    {reasoning_html}
</div>

{prefs_html}

<div class="voice-pref">
    <strong>Voice:</strong>
    <label><input type="radio" name="voice" value="both" checked> Both (compare)</label>
    <label><input type="radio" name="voice" value="adam"> Adam only</label>
    <label><input type="radio" name="voice" value="bella"> Bella only</label>
</div>

{days_block}

<h2 class="library-heading">Practice Library</h2>
<p class="library-intro">
    Available any day, any number of times. These are the supporting practices your daily
    composition references — breath patterns, mindfulness, pre-session prep. The full app
    will surface these contextually; here they're all listed.
</p>

<div class="library-grid">
{library_block}
</div>

<footer>
    Started {start_date.isoformat()} • Day {current_day_idx + 1} of 7 today<br>
    Audio files: <code>audio_output/onboarding/*.mp3</code><br>
    Diagnostic state: <code>state/diagnostic.json</code>
</footer>

<script>
    document.querySelectorAll('input[name="voice"]').forEach(input => {{
        input.addEventListener('change', e => {{
            document.body.classList.remove('hide-adam', 'hide-bella');
            if (e.target.value === 'adam') document.body.classList.add('hide-bella');
            if (e.target.value === 'bella') document.body.classList.add('hide-adam');
        }});
    }});
</script>

</body>
</html>
"""


def write_html(state: dict) -> None:
    html = build_html(state)
    HTML_OUTPUT.write_text(html, encoding="utf-8")
    print(f"  Wrote {HTML_OUTPUT.relative_to(ROOT)}")


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Cadence onboarding test harness.")
    parser.add_argument("--rebuild-html", action="store_true",
                        help="Just rebuild the HTML from saved state, no diagnostic, no generation.")
    parser.add_argument("--reset", action="store_true",
                        help="Delete saved diagnostic state and start fresh.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run diagnostic + build HTML but skip API calls.")
    parser.add_argument("--skip-audio", action="store_true",
                        help="Don't generate audio. Useful when audio already exists or you just want to test routing.")
    parser.add_argument("--skip-library", action="store_true",
                        help="Generate week 1 core audio but skip the practice library (breath, mindfulness, pre-session prep).")
    args = parser.parse_args()

    if args.reset:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
            print(f"  Removed {STATE_FILE.relative_to(ROOT)}")
        if HTML_OUTPUT.exists():
            HTML_OUTPUT.unlink()
            print(f"  Removed {HTML_OUTPUT.relative_to(ROOT)}")
        print("  Reset complete. Run `python onboarding.py` to start over.")
        return 0

    if args.rebuild_html:
        state = load_state()
        if state is None:
            print("  No saved state found. Run `python onboarding.py` first.")
            return 1
        print(f"  Rebuilding HTML from {STATE_FILE.relative_to(ROOT)}…")
        write_html(state)
        print(f"\n  Open {HTML_OUTPUT.relative_to(ROOT)} in your browser.")
        return 0

    # Default flow: diagnostic → save state → generate audio → build HTML
    state = load_state()
    if state is not None:
        print(f"\n  Existing diagnostic found ({STATE_FILE.relative_to(ROOT)}):")
        print(f"  Variant {state['result']['variant']} ({VARIANT_NAMES.get(state['result']['variant'], '?')})")
        print(f"  Started {state['start_date']}")
        print()
        choice = input("  Use this existing diagnostic? [Y/n] ").strip().lower()
        if choice in ("", "y", "yes"):
            print("  Using existing diagnostic.")
        else:
            state = run_diagnostic()
            save_state(state)
    else:
        state = run_diagnostic()
        save_state(state)

    variant = state["result"]["variant"]

    if not args.skip_audio:
        print()
        print(_hr("─"))
        print(f"  Generating Variant {variant} week 1 audio (Adam + Bella).")
        print(_hr("─"))
        summary = generate_week1_audio(variant, dry_run=args.dry_run)
        print()
        if summary["failed"] > 0:
            print("  ⚠ Some files failed to generate. You can re-run this script to retry.")

        if not args.skip_library:
            print()
            print(_hr("─"))
            print("  Generating practice library audio (5 items × Adam + Bella).")
            print(_hr("─"))
            lib_summary = generate_library_audio(dry_run=args.dry_run)
            print()
            if lib_summary["failed"] > 0:
                print("  ⚠ Some library files failed to generate. Re-run to retry.")
        else:
            print("\n  Skipping practice library generation (--skip-library).")
    else:
        print("\n  Skipping all audio generation (--skip-audio).")

    print()
    print(_hr("─"))
    print("  Building HTML page.")
    print(_hr("─"))
    write_html(state)

    print()
    print(_hr("═"))
    print("  Done.")
    print(_hr("═"))
    print(f"\n  Open this in your browser: {HTML_OUTPUT.relative_to(ROOT)}")
    print(f"\n  Tomorrow, re-run with --rebuild-html to update which day is highlighted as today:")
    print(f"      python onboarding.py --rebuild-html")
    print()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  Cancelled.\n")
        sys.exit(0)
