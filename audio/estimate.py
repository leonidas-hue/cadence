"""Estimate the total cost of generating audio for the full Cadence library.

ElevenLabs Multilingual v2 charges 1 credit per character of input.
The dollar value of a credit depends on the subscription plan:

  Free:     10,000 credits/month, no commercial use
  Starter:  30,000 credits/mo at $5      → $0.000167/credit  → $0.167 per 1k chars
  Creator:  100,000 credits/mo at $22    → $0.000220/credit  → $0.220 per 1k chars
  Pro:      500,000 credits/mo at $99    → $0.000198/credit  → $0.198 per 1k chars
  Scale:    2,000,000 credits/mo at $330 → $0.000165/credit  → $0.165 per 1k chars
  Business: 11,000,000 credits/mo at $1,320 → $0.000120/credit → $0.120 per 1k chars

Plus there's a "credit multiplier" for v2 vs other models. v2 is 1x. v3 is also 1x.
Flash is 0.5x. So cost = total_chars * cost_per_credit.

Generating both Adam and Bella means doubling the character count.

Output: total chars, jobs counted, projected cost across plans.
"""

from __future__ import annotations

from pathlib import Path

from .parser import parse_content_dir
from .render import render_for_tts


# Cost per character in USD on each plan, sourced from elevenlabs.io/pricing.
# Reasonable defaults for 2026; verify before running production billing.
PLAN_COST_PER_CHAR_USD = {
    "Starter ($5/mo)": 0.000167,
    "Creator ($22/mo)": 0.000220,
    "Pro ($99/mo)": 0.000198,
    "Scale ($330/mo)": 0.000165,
    "Business ($1,320/mo)": 0.000120,
}


def estimate_all() -> None:
    content_dir = Path(__file__).resolve().parent.parent / "content"
    jobs = parse_content_dir(content_dir)

    by_variant: dict[str, list[int]] = {"a": [], "b": [], "c": [], "d": []}
    branched_chars = 0
    long_pause_total = 0
    warnings_total = 0
    huge_pause_count = 0  # pauses ≥30s

    print(f"Estimating cost across {len(jobs)} session jobs.\n")

    for job in jobs:
        rendered = render_for_tts(job.body_md)
        by_variant[job.variant].append(rendered.char_count)
        if job.branch:
            branched_chars += rendered.char_count
        long_pause_total += len(rendered.long_pauses)
        warnings_total += len(rendered.warnings)
        for p in rendered.long_pauses:
            if p >= 30:
                huge_pause_count += 1

    # Per-variant breakdown
    print(f"{'Variant':<10} {'Sessions':>10} {'Chars':>10} {'Avg/session':>14}")
    print("-" * 50)
    grand_total = 0
    for variant in ("a", "b", "c", "d"):
        chars = by_variant[variant]
        n = len(chars)
        total = sum(chars)
        avg = total // n if n else 0
        grand_total += total
        print(f"{variant.upper():<10} {n:>10d} {total:>10,d} {avg:>14,d}")

    print("-" * 50)
    print(f"{'TOTAL':<10} {len(jobs):>10d} {grand_total:>10,d}")
    print()

    # Two-voice production
    both_voices_total = grand_total * 2
    print(f"Single-voice production (Adam OR Bella): {grand_total:,} characters")
    print(f"Two-voice production (Adam AND Bella):   {both_voices_total:,} characters")
    print()

    # Cost projections
    print("Projected cost by plan, two-voice production:\n")
    print(f"  {'Plan':<22} {'Cost (USD)':>12}")
    print("  " + "-" * 36)
    for plan, rate in PLAN_COST_PER_CHAR_USD.items():
        cost = both_voices_total * rate
        print(f"  {plan:<22} ${cost:>11,.2f}")
    print()

    # Coverage notes
    print("Notes:")
    print(f"  - {len([j for j in jobs if j.branch])} jobs are branched variants "
          f"({branched_chars:,} chars)")
    print(f"  - {long_pause_total} sessions contain long-pause warnings")
    print(f"  - {huge_pause_count} sessions contain pauses ≥30s "
          "(silence segments, recommend splitting audio)")
    print(f"  - {warnings_total} total renderer warnings — review before production")
    print()
    print("Recommendation: start with the pilot (Variant A week 1, both voices).")
    print(f"  Pilot cost: ~$5-10 depending on plan.")
    print(f"  Full project at Pro tier: ~${both_voices_total * 0.000198:,.2f}")


if __name__ == "__main__":
    estimate_all()
