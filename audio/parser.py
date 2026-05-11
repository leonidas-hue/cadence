"""Parse Cadence content markdown files into structured audio jobs.

Each session in a script file becomes one or more AudioJobs (more than one when
the session is branched, e.g., Variant D Day 22 has both _current and _past versions).

Run as a script to validate parsing across all content files:
    python audio/parser.py

Usage as a library:
    from audio.parser import parse_content_dir
    jobs = parse_content_dir("content")
    for job in jobs:
        print(job.audio_filename())
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# Variant codes from filename → letter used in audio filenames
VARIANT_CODES = {
    "variant_a": "a",
    "variant_b": "b",
    "variant_c": "c",
    "variant_d": "d",
}


@dataclass
class AudioJob:
    """One generation task. Renders to one MP3 per voice (Adam, Bella)."""

    variant: str            # 'a', 'b', 'c', 'd'
    week: int               # 1-8
    day: int                # 1-56
    slug: str               # short kebab-case title
    branch: Optional[str]   # 'current' / 'past' / None
    title: str              # the human title
    body_md: str            # raw markdown body of the session (script only)
    source_file: str        # path it came from

    def audio_filename(self, voice: str) -> str:
        """Returns e.g. 'a_1_3_first-kegel-session_adam.mp3' or
        'd_4_22_first-step_current_adam.mp3'."""
        parts = [self.variant, str(self.week), str(self.day), self.slug]
        if self.branch:
            parts.append(self.branch)
        parts.append(voice.lower())
        return "_".join(parts) + ".mp3"

    def session_id(self) -> str:
        """A stable ID for this session (no voice suffix)."""
        parts = [self.variant, f"w{self.week}", f"d{self.day}", self.slug]
        if self.branch:
            parts.append(self.branch)
        return "_".join(parts)


# ------------------------------------------------------------------
# Filename → (variant, weeks_covered)
# ------------------------------------------------------------------

FILENAME_PATTERN = re.compile(
    r"^(variant_[abcd])_(?:week_(\d+)|weeks_(\d+)_to_(\d+))\.md$"
)


def parse_filename(path: Path) -> tuple[str, list[int]]:
    """Returns (variant_code, list_of_weeks_in_file).
    Raises ValueError if filename doesn't match a known content file pattern."""
    m = FILENAME_PATTERN.match(path.name)
    if not m:
        raise ValueError(f"Not a recognized content filename: {path.name}")

    variant_full = m.group(1)
    variant = VARIANT_CODES[variant_full]

    if m.group(2):  # single week
        weeks = [int(m.group(2))]
    else:
        start, end = int(m.group(3)), int(m.group(4))
        weeks = list(range(start, end + 1))

    return variant, weeks


# ------------------------------------------------------------------
# Session header parsing
# ------------------------------------------------------------------

# `# Session 14 — "Closing the week"` or
# `## Session 41 — "Where you are"` or
# `# Session 18p — "..."` (Variant A path-letter suffix) or
# `# Day 22 — "..."` (Variant D weeks 4-5)
SESSION_HEADER = re.compile(
    r"^#{1,3}\s*(?:Session|Day)\s+(\d+)([a-z]?)\s*[—\-]\s*\"([^\"]+)\""
)

# `**Day:** 14` line in frontmatter (sometimes inline in compressed week files)
DAY_LINE = re.compile(r"\*\*Day:\*\*\s*(\d+)")

# Compact form in 5_to_8 files: `**Day:** 38 · ~6 min · ...`
COMPACT_HEADER = re.compile(
    r"^#{1,3}\s*Session\s+(\d+)\s*[—\-]\s*\"([^\"]+)\""
)

# Branch markers from Variant D
BRANCH_HEADER = re.compile(
    r"^#{2,4}\s*Version\s+([AB])\s*[—\-]\s*(Current|Past)\s+path", re.IGNORECASE
)
# Some variants use a different branched format
DAY_BRANCH_HEADER = re.compile(r"^#\s*Day\s+(\d+)\s*[—\-]\s*\"([^\"]+)\"")


# Map Variant A session-letter suffixes to branch names
SUFFIX_TO_BRANCH = {
    "p": "partnered",
    "s": "solo",
    "n": "declined",  # partner-declined path
}


def slugify(title: str) -> str:
    """'First Kegel session' → 'first-kegel-session'"""
    s = title.lower()
    s = re.sub(r"[^\w\s-]", "", s)  # strip punctuation
    s = re.sub(r"\s+", "-", s.strip())
    return s


def week_for_day(day: int) -> int:
    """Day 1 → week 1, Day 8 → week 2, ..., Day 56 → week 8."""
    return ((day - 1) // 7) + 1


# ------------------------------------------------------------------
# Convention stripping (for character counts and rendering)
# ------------------------------------------------------------------

# Stage directions in parens at the start of a line: (Audio cues...)
STAGE_DIRECTION = re.compile(r"^\([^)]*\)\s*$", re.MULTILINE)

# Tone markers: [soft], [firmer]
TONE_MARKER = re.compile(r"\[(soft|firmer|whispered|warm)\]\s*", re.IGNORECASE)

# Inline directives we keep but don't speak:
PAUSE_MARKER = re.compile(r"\[PAUSE\s+(\d+)s\]", re.IGNORECASE)
BREATH_IN_MARKER = re.compile(r"\[BREATH IN\s*[—\-]\s*(\d+)s\]", re.IGNORECASE)
BREATH_OUT_MARKER = re.compile(r"\[BREATH OUT\s*[—\-]\s*(\d+)s\]", re.IGNORECASE)
INHALE_MARKER = re.compile(r"\[INHALE\]", re.IGNORECASE)
EXHALE_MARKER = re.compile(r"\[EXHALE\]", re.IGNORECASE)


def strip_speakable_markers(text: str) -> str:
    """Removes [soft] / [firmer] / stage directions / italic emphasis markdown.
    Used for character counts and clean rendering."""
    text = STAGE_DIRECTION.sub("", text)
    text = TONE_MARKER.sub("", text)
    # remove markdown italics (single underscore or asterisk pairs)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    return text


# ------------------------------------------------------------------
# Content body extraction
# ------------------------------------------------------------------


def split_session_chunks(file_text: str) -> list[tuple[int, int, str, str, str]]:
    """Walks the file and returns a list of
    (line_number, day, suffix, title, body) for each session encountered.

    `suffix` is '' for unsuffixed Sessions, or 'p'/'s'/'n' for Variant A path
    sessions, or '' for Variant D `# Day N` headings (the branch is detected
    later via Version A/B markers inside the body).

    Body is the text between the session's `---` separator (after frontmatter)
    and the next session's heading (or end of file).
    """
    chunks: list[tuple[int, int, str, str, str]] = []
    lines = file_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = SESSION_HEADER.match(line)
        if not m:
            i += 1
            continue

        day_from_header = int(m.group(1))
        suffix = m.group(2) or ""
        title = m.group(3)
        header_line_no = i

        # Find the day from frontmatter — usually matches header, but verify.
        # Variant A uses '**Day:** 18, partnered path' which still parses to 18.
        day = day_from_header
        for j in range(i + 1, min(i + 10, len(lines))):
            m_day = DAY_LINE.search(lines[j])
            if m_day:
                day = int(m_day.group(1))
                break

        # Find body_start at first `---` line after the session header
        body_start = None
        for j in range(i + 1, min(i + 25, len(lines))):
            if lines[j].strip() == "---":
                body_start = j + 1
                break

        if body_start is None:
            body_start = i + 1

        # Find body_end: next session header or top-level Week heading or EOF
        body_end = len(lines)
        for j in range(body_start, len(lines)):
            if SESSION_HEADER.match(lines[j]):
                body_end = j
                break
            if lines[j].strip().startswith("# Week ") and lines[j].startswith("# "):
                body_end = j
                break

        body = "\n".join(lines[body_start:body_end]).strip()
        chunks.append((header_line_no, day, suffix, title, body))
        i = body_end

    return chunks


def detect_branches(body: str) -> list[tuple[Optional[str], str]]:
    """If a session body has branches (Version A — Current / Version B — Past),
    splits into multiple (branch_name, body_chunk) pairs.
    Returns [(None, body)] if no branching."""
    if not BRANCH_HEADER.search(body):
        return [(None, body)]

    branches: list[tuple[str, str]] = []
    lines = body.splitlines()
    current_branch: Optional[str] = None
    current_lines: list[str] = []

    for line in lines:
        m = BRANCH_HEADER.match(line)
        if m:
            # Save previous branch (if any meaningful content)
            if current_branch is not None and current_lines:
                branches.append((current_branch, "\n".join(current_lines).strip()))
            elif current_lines and current_branch is None:
                # discard preamble between session header and first branch
                pass
            current_branch = m.group(2).lower()  # 'current' or 'past'
            current_lines = []
        else:
            current_lines.append(line)

    if current_branch is not None and current_lines:
        branches.append((current_branch, "\n".join(current_lines).strip()))

    return branches if branches else [(None, body)]


# ------------------------------------------------------------------
# Top-level: parse one file or whole directory
# ------------------------------------------------------------------


def parse_file(path: Path) -> list[AudioJob]:
    """Returns all AudioJobs from a single content markdown file."""
    variant, _expected_weeks = parse_filename(path)
    text = path.read_text(encoding="utf-8")
    jobs: list[AudioJob] = []

    for line_no, day, suffix, title, body in split_session_chunks(text):
        slug = slugify(title)
        week = week_for_day(day)

        # If session header had a path-letter suffix (Variant A: 18p/18s/18n),
        # that's the branch and there's no further internal branching.
        if suffix:
            branch = SUFFIX_TO_BRANCH.get(suffix, suffix)
            jobs.append(
                AudioJob(
                    variant=variant,
                    week=week,
                    day=day,
                    slug=slug,
                    branch=branch,
                    title=title,
                    body_md=body,
                    source_file=str(path),
                )
            )
            continue

        # Otherwise, check for internal Version A/B branching (Variant D)
        branches = detect_branches(body)
        for branch, branch_body in branches:
            if not branch_body.strip():
                continue
            jobs.append(
                AudioJob(
                    variant=variant,
                    week=week,
                    day=day,
                    slug=slug,
                    branch=branch,
                    title=title,
                    body_md=branch_body,
                    source_file=str(path),
                )
            )

    return jobs


def parse_content_dir(content_dir: str | Path) -> list[AudioJob]:
    """Returns all AudioJobs from every variant_*.md file in the dir.
    Skips _tracker.md, shared_*.md, addon_*.md (those aren't session scripts)."""
    content_dir = Path(content_dir)
    jobs: list[AudioJob] = []
    for path in sorted(content_dir.iterdir()):
        if not path.is_file() or path.suffix != ".md":
            continue
        if not path.name.startswith("variant_"):
            continue
        try:
            jobs.extend(parse_file(path))
        except ValueError:
            continue

    # Sort: variant, day, branch (None first, then alphabetical)
    jobs.sort(key=lambda j: (j.variant, j.day, j.branch or ""))
    return jobs


# ------------------------------------------------------------------
# Validation / smoke test
# ------------------------------------------------------------------


def validate_jobs(jobs: list[AudioJob]) -> list[str]:
    """Returns a list of warnings/errors. Empty list = clean parse."""
    issues: list[str] = []
    seen_filenames: dict[str, str] = {}
    by_variant_day: dict[tuple[str, int], list[AudioJob]] = {}

    for j in jobs:
        # 1) Filename uniqueness per voice
        for voice in ("adam", "bella"):
            fn = j.audio_filename(voice)
            if fn in seen_filenames:
                issues.append(
                    f"Duplicate filename {fn} (from {j.source_file} and {seen_filenames[fn]})"
                )
            else:
                seen_filenames[fn] = j.source_file

        # 2) Body is non-trivial
        clean = strip_speakable_markers(j.body_md)
        word_count = len(clean.split())
        if word_count < 30:
            issues.append(
                f"{j.session_id()} has only {word_count} words after stripping markers — "
                f"verify it's complete"
            )

        # 3) Group by (variant, day) to check expected counts later
        by_variant_day.setdefault((j.variant, j.day), []).append(j)

    # 4) Each variant should have days 1..56 covered
    for variant in ("a", "b", "c", "d"):
        days_present = {d for (v, d) in by_variant_day if v == variant}
        missing = set(range(1, 57)) - days_present
        if missing:
            issues.append(f"Variant {variant.upper()} missing days: {sorted(missing)}")

    # 5) Any day with multiple jobs should have a recognized branch set
    valid_branch_sets = [
        {"current", "past"},
        {"partnered", "solo", "declined"},
        {"partnered", "solo"},  # In case declined branch isn't applicable
    ]
    for (variant, day), js in by_variant_day.items():
        branches = {j.branch for j in js if j.branch}
        if len(js) > 1:
            if branches not in valid_branch_sets:
                issues.append(
                    f"Variant {variant.upper()} day {day} has {len(js)} jobs with branches {branches}"
                )

    return issues


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    content_dir = Path(__file__).resolve().parent.parent / "content"
    jobs = parse_content_dir(content_dir)

    print(f"Parsed {len(jobs)} audio jobs from {content_dir}")
    by_variant: dict[str, int] = {}
    branched_count = 0
    for j in jobs:
        by_variant[j.variant] = by_variant.get(j.variant, 0) + 1
        if j.branch:
            branched_count += 1

    for v in sorted(by_variant):
        print(f"  Variant {v.upper()}: {by_variant[v]} jobs")
    print(f"  Branched jobs: {branched_count}")
    print()

    issues = validate_jobs(jobs)
    if issues:
        print(f"⚠  {len(issues)} issues found:")
        for issue in issues[:30]:
            print(f"   {issue}")
        if len(issues) > 30:
            print(f"   ... and {len(issues) - 30} more")
        sys.exit(1)
    else:
        print("✓ All parses clean. No duplicate filenames, no missing days.")
