"""Generate the Cadence pilot batch and produce a listening checklist.

The pilot is Variant A week 1: 7 sessions × 2 voices = 14 audio files.
Total chars: ~17,700 × 2 = ~35,400 chars.
Expected cost on Pro plan: ~$7.

After running, listen to all 14 files end-to-end with the listening checklist.
The point isn't to verify each session in isolation — it's to surface the
systematic issues (pacing, breath cue feel, voice character) that affect
every session in the library before scaling production.

Usage:
    export ELEVENLABS_API_KEY=sk-xxx
    python -m audio.pilot           # actually generate
    python -m audio.pilot --dry-run # see what would happen, no API calls
"""

from __future__ import annotations

import sys
from pathlib import Path

from .generate import generate_jobs, DEFAULT_OUTPUT_DIR
from .parser import parse_content_dir


PILOT_OUTPUT_DIR = DEFAULT_OUTPUT_DIR / "pilot"


LISTENING_CHECKLIST = """
LISTENING CHECKLIST — Cadence Pilot (Variant A Week 1)

Listen to all 14 files (7 sessions × 2 voices) end-to-end.
Compare Adam vs Bella for each session — they should land equivalently
even though the voices differ in gender register.

For each session, evaluate:

  PACING
  □  Does the voice rush during instructions, or stay measured?
  □  Are pauses too short, too long, or right?
  □  Do breath cue durations match the voice's natural breathing?
     (e.g. [BREATH IN — 4s] should give the listener a 4-second window)

  TONE
  □  Does the voice match the protocol's "calm, measured, warm but not soft"
     direction? Or does it veer wellness-influencer or clinical-cold?
  □  Does the voice have noticeable vocal fry or rising intonation?
     (We want neither.)
  □  Does the voice maintain the same character across all 7 sessions?

  BREATH CUES
  □  Do the breath-pause durations feel right for actual paced breathing?
  □  Are the breath markers too dense in any session?
  □  Day 2 ("Extended exhale breathing") is the most breath-heavy session —
     listen carefully to whether the user could realistically follow along.

  CONTENT FAITHFULNESS
  □  Does any technical term get mispronounced consistently? Note them for
     pronunciation override before full production.
  □  "Kegel" is the most likely candidate. Listen.
  □  "Diaphragmatic" — does it land cleanly?
  □  "IELT" — likely read letter-by-letter, which is fine.

  ARTIFACTS
  □  Any audible audio artifacts (clicks, speed-up bursts, glitches)?
  □  Long-pause sessions — Day 2 has a 90s pause, Day 5 has a 120s pause.
     Did the chained <break> tags produce clean silence, or did the audio
     do something weird?
  □  Any sessions where the voice changes character mid-session?

  EMOTIONAL FIT
  □  Does Day 1 ("Why this works") set the right tone for the protocol?
     This is the user's first impression — is it warm, credible, grounded?
  □  Does Day 4 ("Spectatoring") land with the right note of seriousness
     without becoming heavy?
  □  Does Day 7 (closing) feel like a genuine consolidation, or rote?

DECISIONS TO MAKE AFTER LISTENING

  □  Voice settings: do stability 0.55 / similarity 0.75 / style 0.15 work,
     or do we need to retune? (Higher stability = more consistent, less
     expressive. Lower stability = more variation, may drift in long sessions.)
  □  Adam vs Bella vs both: do we ship both as user choice, or pick one?
  □  Long pauses (≥10s): for production, should we (a) split audio at those
     points and let the app insert silence, or (b) accept chained breaks?
  □  Pronunciation overrides: any words that need explicit phoneme tags
     (only available on Flash v2 / English v1, would mean different model)
     or text substitutions (e.g., "K-E-G-EL" instead of "Kegel")?
  □  Any sessions that need re-writing for audio? Some things read well on
     paper but feel awkward when voiced.

NEXT STEPS AFTER PILOT VALIDATION

  1. Apply any voice setting changes to voices.json
  2. Apply any script edits surfaced by listening
  3. Run: python -m audio.generate --all
  4. Audit a random sample (5%) of the full output for systematic issues
"""


def main() -> int:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args

    content_dir = Path(__file__).resolve().parent.parent / "content"
    all_jobs = parse_content_dir(content_dir)

    pilot_jobs = [j for j in all_jobs if j.variant == "a" and j.week == 1]

    if not pilot_jobs:
        print("ERROR: no pilot jobs found. Check that content/variant_a_week_1.md exists.")
        return 1

    print(f"PILOT: {len(pilot_jobs)} sessions × 2 voices = {len(pilot_jobs) * 2} files")
    print(f"Output: {PILOT_OUTPUT_DIR}")
    if dry_run:
        print("DRY RUN — no API calls will be made.\n")

    generate_jobs(pilot_jobs, output_dir=PILOT_OUTPUT_DIR, dry_run=dry_run)

    if not dry_run:
        # Save the checklist alongside the audio
        checklist_path = PILOT_OUTPUT_DIR / "LISTENING_CHECKLIST.txt"
        PILOT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        checklist_path.write_text(LISTENING_CHECKLIST)
        print(f"\nListening checklist written to: {checklist_path}")
        print("Listen to all 14 files end-to-end before deciding on full production.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
