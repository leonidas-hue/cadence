"""
Cadence — Diagnostic Routing Logic

Takes responses to the diagnostic questionnaire and routes the user into
one of four protocol variants. The priority ordering is intentional:
hypertonic users MUST be caught first because standard advice can harm them.

Variants:
    A — Anxiety-Driven Acquired PE
    B — Hypertonic Pelvic Floor (safety-critical routing)
    C — Lifelong / Hypotonic PE
    D — Porn-Conditioned / Masturbation-Pattern PE

Returns a dict with:
    variant: str           — one of 'A', 'B', 'C', 'D'
    name: str              — human-readable variant name
    reasoning: list[str]   — why this variant was chosen
    flags: list[str]       — additional flags for protocol customization
    scores: dict           — raw scores for transparency / debugging
    severity: str          — 'mild' / 'moderate' / 'severe' from PEDT-5
"""

from typing import Any


# -----------------------------------------------------------------------------
# Scoring helpers
# -----------------------------------------------------------------------------

def _score_pedt5(responses: dict[str, int]) -> int:
    """Sum the 5 PEDT items. Each is 0-4. Total is 0-20."""
    return sum(responses[f"pedt5_{i}"] for i in range(1, 6))


def _score_hypertonic(responses: dict[str, bool]) -> int:
    """Count yes responses across the 7 hypertonic items."""
    return sum(1 for i in range(1, 8) if responses[f"hyper_{i}"])


def _classify_pedt5(score: int) -> str:
    if score >= 11:
        return "pe"
    if score >= 9:
        return "probable_pe"
    return "no_pe"


def _classify_severity(pedt5_score: int) -> str:
    if pedt5_score >= 16:
        return "severe"
    if pedt5_score >= 11:
        return "moderate"
    if pedt5_score >= 9:
        return "mild"
    return "subclinical"


# -----------------------------------------------------------------------------
# Routing
# -----------------------------------------------------------------------------

def route(responses: dict[str, Any]) -> dict[str, Any]:
    """
    Route a user to one of the four protocol variants.

    `responses` is expected to be a flat dict with keys matching the question
    IDs in questions.json. See the test file for examples.
    """
    # --- Score the validated instruments ------------------------------------
    pedt5_score = _score_pedt5(responses)
    pedt5_class = _classify_pedt5(pedt5_score)
    severity = _classify_severity(pedt5_score)

    hypertonic_score = _score_hypertonic(responses)

    # --- Extract individual signals -----------------------------------------
    onset = responses["onset_when"]
    porn_freq = responses["mast_porn_freq"]                # 0-5
    grip = responses["mast_grip"]                          # 0-3
    pace = responses["mast_pace"]                          # 0-3
    porn_dependency = responses["mast_without_porn"]       # 0-3
    porn_history = responses.get("mast_porn_history", "never")  # 'never' / 'past_stopped' / 'past_recent' / 'current'
    ielt = responses["baseline_ielt"]                      # minutes (or -1)
    anxiety = responses["baseline_anxiety"]                # 0-4

    scores = {
        "pedt5_total": pedt5_score,
        "pedt5_classification": pedt5_class,
        "hypertonic_total": hypertonic_score,
        "estimated_ielt_minutes": ielt,
        "anxiety_self_report": anxiety,
        "porn_history": porn_history,
    }

    # --- Subclinical short-circuit ------------------------------------------
    # If PEDT-5 is in the no-PE band AND no other signal is strong, advise the
    # user the program may not be needed. We still let them continue if they want.
    porn_history_signal = (
        responses.get("mast_porn_history", "never") in ("past_recent", "past_stopped", "current")
        and (responses["mast_grip"] >= 2 or responses["mast_pace"] >= 2)
    )
    subclinical = (
        pedt5_class == "no_pe"
        and hypertonic_score < 3
        and not (porn_freq >= 3 and porn_dependency >= 2)
        and not porn_history_signal
        and (ielt < 0 or ielt >= 3.0)
    )

    # --- Priority 1: Hypertonic floor (SAFETY-CRITICAL) ---------------------
    # This routing must come first. Putting a hypertonic user through standard
    # Kegel work makes their condition worse.
    if hypertonic_score >= 3:
        return {
            "variant": "B",
            "name": "Hypertonic Pelvic Floor",
            "reasoning": [
                f"You showed {hypertonic_score} of 7 indicators of pelvic floor tension. "
                f"This pattern is common but often missed.",
                "Standard Kegel exercises are not appropriate as a starting point for this profile "
                "and can make symptoms worse. Your protocol prioritizes pelvic floor relaxation, "
                "diaphragmatic breathing, and hip mobility instead.",
                "Strong recommendation: see a pelvic floor physiotherapist alongside this program. "
                "Cadence is most effective as a supplement to in-person care for this profile.",
            ],
            "flags": ["hypertonic", "recommend_pt", "no_standard_kegels_initially"],
            "scores": scores,
            "severity": severity,
        }

    # --- Priority 2: Porn-conditioned / sensitization -----------------------
    # Catches both current heavy users AND past heavy users with residual
    # grip/pace patterns. The conditioning persists after porn use stops —
    # what we're really detecting is the recalibration need, not active use.
    porn_heavy_current = porn_freq >= 3                  # daily or more, currently
    porn_heavy_past = porn_history in ("past_recent", "past_stopped")
    porn_heavy_either = porn_heavy_current or porn_heavy_past
    grip_intense = grip >= 2                             # firm or very firm
    pace_fast = pace >= 2                                # fast or very fast
    porn_dependent = porn_dependency >= 2                # often or always

    if porn_heavy_either and (grip_intense or pace_fast or porn_dependent):
        # Distinguish current vs past for content branching (e.g. week 4 taper)
        is_current = porn_heavy_current or porn_history == "current"
        flags = ["porn_conditioned", "recondition"]
        if is_current:
            flags.append("porn_current")
            flags.append("porn_taper")  # week 4 taper module applies
            reasoning_lead = (
                "Heavy current pornography use is combined with conditioning signals "
                "(grip pressure, pace, or stimulus dependency)."
            )
        else:
            flags.append("porn_past")
            # Note: no porn_taper flag — the taper module is skipped for past users
            reasoning_lead = (
                "Past heavy pornography use is combined with persistent conditioning signals "
                "(grip pressure, pace, or stimulus dependency). Patterns established during "
                "heavy use often persist long after the use itself has stopped."
            )

        return {
            "variant": "D",
            "name": "Porn-Conditioned / Masturbation-Pattern",
            "reasoning": [
                reasoning_lead,
                "Your nervous system has likely calibrated to a level of stimulation that's "
                "difficult to replicate with a partner. The protocol focuses on recalibrating "
                "your masturbation patterns and arousal thresholds.",
                "Pelvic floor work is included but is not the primary lever for your profile.",
            ],
            "flags": flags,
            "scores": scores,
            "severity": severity,
        }

    # --- Priority 3: Lifelong / hypotonic -----------------------------------
    # Lifelong PE with very short baseline IELT signals a more neurobiological
    # profile. These users benefit from longer behavioral protocols and are
    # the most likely to want pharma options as a bridge.
    lifelong_with_short_ielt = (
        onset == "lifelong"
        and (ielt < 0 or ielt < 1.5)
    )
    if lifelong_with_short_ielt:
        return {
            "variant": "C",
            "name": "Lifelong / Hypotonic PE",
            "reasoning": [
                "Lifelong onset combined with a very short baseline IELT suggests a profile "
                "that's more neurobiological than situational.",
                "Your protocol builds pelvic floor control progressively over 8-12 weeks "
                "and integrates edging practice. Behavioral training will take longer for this "
                "profile, which is normal — be patient.",
                "Pharmacological options (dapoxetine, topical lidocaine) are covered as "
                "educational content. They can serve as a legitimate bridge while you build skills.",
            ],
            "flags": ["lifelong", "consider_pharma", "extended_timeline"],
            "scores": scores,
            "severity": severity,
        }

    # --- Subclinical advisory (route to A but flag) -------------------------
    if subclinical:
        return {
            "variant": "A",
            "name": "Anxiety-Driven Acquired PE (subclinical advisory)",
            "reasoning": [
                "Your PEDT-5 score is in the range that does not indicate clinically significant PE.",
                "If you'd like to build greater control and presence regardless, this protocol "
                "still works well — but you may not need a full intervention.",
                "Consider whether the underlying issue is performance anxiety rather than "
                "ejaculatory timing per se.",
            ],
            "flags": ["subclinical", "anxiety", "optional_program"],
            "scores": scores,
            "severity": severity,
        }

    # --- Priority 4 (default): Anxiety-driven acquired ----------------------
    return {
        "variant": "A",
        "name": "Anxiety-Driven Acquired PE",
        "reasoning": [
            "Your profile points to acquired PE driven primarily by performance anxiety "
            "rather than pelvic floor dysfunction or stimulus conditioning.",
            "The protocol emphasizes breathwork, parasympathetic activation, cognitive "
            "restructuring, and sensate-focus principles. Pelvic floor work is included but light.",
            "This is generally a more responsive profile than lifelong PE — there's a clear "
            "cause (anxiety) that the protocol directly targets. Most users start to notice "
            "changes by week 4-6, though everyone's timeline is different.",
        ],
        "flags": ["anxiety", "acquired"] + (["high_anxiety"] if anxiety >= 3 else []),
        "scores": scores,
        "severity": severity,
    }


# -----------------------------------------------------------------------------
# Convenience: pretty-print a routing result
# -----------------------------------------------------------------------------

def format_result(result: dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 70)
    lines.append(f"  PROTOCOL VARIANT {result['variant']}: {result['name']}")
    lines.append("=" * 70)
    lines.append("")
    lines.append("Why this protocol:")
    for r in result["reasoning"]:
        lines.append(f"  • {r}")
    lines.append("")
    lines.append("Scores:")
    for k, v in result["scores"].items():
        lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append(f"Severity: {result['severity']}")
    lines.append(f"Flags: {', '.join(result['flags']) if result['flags'] else '(none)'}")
    lines.append("=" * 70)
    return "\n".join(lines)
