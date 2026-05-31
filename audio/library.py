"""Parse standalone practice-library scripts into audio jobs.

These are content files that aren't part of any variant's 8-week structured
program but are available to the user any time:

- shared_breathwork_practice.md   → 3 breath patterns (Calm, Ground, Settle)
- addon_mindfulness_daily.md      → daily mindfulness session
- shared_pre_session_prep.md      → pre-partnered-sex prep

Intentionally NOT included here:
- shared_edging_solo.md       — gated by program week, not freely available
- shared_ielt_tutorial.md     — reference content, not practice
- shared_journaling_prompts.md — text-only spec, no audio

The LibraryJob shape mirrors AudioJob's duck-typed interface (body_md +
audio_filename) so the existing generate.py machinery works unchanged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LibraryJob:
    """Audio job for a practice-library item. Duck-types AudioJob for generate.py."""

    slug: str           # 'breath-calm', 'mindfulness-daily', etc.
    title: str          # human title for HTML display
    duration: str       # rough duration string for HTML (e.g., '~5 min')
    use_case: str       # short description for HTML
    body_md: str        # raw script body for the renderer
    source_file: str    # path it came from

    def audio_filename(self, voice: str) -> str:
        """e.g. 'library_breath-calm_adam.mp3'. The 'library_' prefix keeps
        these visually distinct from variant audio files in the output dir."""
        return f"library_{self.slug}_{voice.lower()}.mp3"

    def session_id(self) -> str:
        return f"library_{self.slug}"


# ---------------------------------------------------------------------------
# The five library items, hand-curated. The slugs and titles are stable —
# the HTML and any future Flutter port references them.
# ---------------------------------------------------------------------------

LIBRARY_ITEMS: list[dict] = [
    {
        "slug": "breath-calm",
        "title": "Breath — Calm",
        "duration": "~5 min",
        "use_case": "Extended exhale (4-in, 6-out). General parasympathetic activation. Default daily practice.",
        "source_file": "shared_breathwork_practice.md",
        "header_pattern": r"^# Pattern 1 — ",
    },
    {
        "slug": "breath-ground",
        "title": "Breath — Ground",
        "duration": "~5 min",
        "use_case": "Box breathing (4-4-4-4). Pre-event grounding when acute pressure shows up.",
        "source_file": "shared_breathwork_practice.md",
        "header_pattern": r"^# Pattern 2 — ",
    },
    {
        "slug": "breath-settle",
        "title": "Breath — Settle",
        "duration": "~5 min",
        "use_case": "4-7-8 breathing. Evening / wind-down. Slower nervous-system settle.",
        "source_file": "shared_breathwork_practice.md",
        "header_pattern": r"^# Pattern 3 — ",
    },
    {
        "slug": "mindfulness-daily",
        "title": "Mindfulness — Daily",
        "duration": "~7 min",
        "use_case": "General attention training. Independent evidence for sexual function (Brotto et al.) when stacked with the protocol.",
        "source_file": "addon_mindfulness_daily.md",
        "header_pattern": r"^# Mindfulness Add-On — ",
    },
    {
        "slug": "pre-session-prep",
        "title": "Pre-session prep — Ready",
        "duration": "~10 min",
        "use_case": "Use 30-60 min before partnered sex. Settles you into parasympathetic state without thinking about performance.",
        "source_file": "shared_pre_session_prep.md",
        "header_pattern": r"^# Pre-Session Prep — ",
    },
]


# ---------------------------------------------------------------------------
# Body extraction
# ---------------------------------------------------------------------------

def _extract_section_body(file_text: str, header_pattern: str) -> str:
    """Returns the script body that follows a matching `# Header` line.

    The body runs from after the next `## Script` marker (if present) or
    after the first `---` divider following the header, up until the next
    top-level `# ` heading or EOF.

    If neither `## Script` nor `---` follows the header, we take everything
    from the line after the header to the next top-level heading."""
    lines = file_text.splitlines()
    pat = re.compile(header_pattern)

    # Find the header
    header_idx = None
    for i, line in enumerate(lines):
        if pat.match(line):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError(f"Header pattern not found: {header_pattern}")

    # Find body start
    body_start = None
    for j in range(header_idx + 1, min(header_idx + 40, len(lines))):
        if lines[j].strip() == "## Script":
            body_start = j + 1
            break
        if lines[j].strip() == "---":
            # First '---' after header — frontmatter divider; body begins after
            body_start = j + 1
            break
    if body_start is None:
        body_start = header_idx + 1

    # Find body end: next top-level `# ` heading
    body_end = len(lines)
    for j in range(body_start, len(lines)):
        if lines[j].startswith("# ") and not lines[j].startswith("## "):
            body_end = j
            break

    return "\n".join(lines[body_start:body_end]).strip()


def parse_library(content_dir: Path | str = None) -> list[LibraryJob]:
    """Returns LibraryJobs for all curated library items."""
    if content_dir is None:
        content_dir = Path(__file__).resolve().parent.parent / "content"
    else:
        content_dir = Path(content_dir)

    jobs: list[LibraryJob] = []
    for item in LIBRARY_ITEMS:
        source_path = content_dir / item["source_file"]
        if not source_path.exists():
            raise FileNotFoundError(
                f"Library source missing: {source_path}. "
                f"Required for job '{item['slug']}'."
            )
        text = source_path.read_text(encoding="utf-8")
        body = _extract_section_body(text, item["header_pattern"])
        jobs.append(
            LibraryJob(
                slug=item["slug"],
                title=item["title"],
                duration=item["duration"],
                use_case=item["use_case"],
                body_md=body,
                source_file=str(source_path),
            )
        )
    return jobs


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    jobs = parse_library()
    print(f"Parsed {len(jobs)} library items:\n")
    for j in jobs:
        words = len(j.body_md.split())
        chars = len(j.body_md)
        print(f"  {j.slug:25s} {j.duration:10s} {words:>5d} words {chars:>6d} chars")
    print()
    print("Audio filenames (both voices):")
    for j in jobs:
        print(f"  {j.audio_filename('adam')}")
        print(f"  {j.audio_filename('bella')}")
