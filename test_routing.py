"""
Tests for the Cadence routing logic.

Each test constructs a plausible response set for a target variant and
checks that the router produces the correct assignment. Run with:

    python -m pytest test_routing.py -v

Or just `python test_routing.py` for the simple harness at the bottom.
"""

from routing import route, format_result


def _base_responses() -> dict:
    """A neutral baseline that scores below all routing thresholds."""
    return {
        # PEDT-5: low scores
        "pedt5_1": 0, "pedt5_2": 0, "pedt5_3": 0, "pedt5_4": 0, "pedt5_5": 0,
        # Hypertonic: all no
        "hyper_1": False, "hyper_2": False, "hyper_3": False, "hyper_4": False,
        "hyper_5": False, "hyper_6": False, "hyper_7": False,
        # Masturbation: low intensity, no porn history
        "mast_porn_freq": 0, "mast_grip": 0, "mast_pace": 0, "mast_without_porn": 0,
        "mast_porn_history": "never",
        # Onset / baseline
        "onset_when": "acquired",
        "baseline_ielt": 5.0,
        "baseline_anxiety": 0,
    }


# -----------------------------------------------------------------------------
# Variant A — Anxiety-Driven Acquired
# -----------------------------------------------------------------------------

def test_variant_a_classic():
    """Acquired onset, anxious profile, normal everything else → A."""
    r = _base_responses()
    r.update({
        "pedt5_1": 3, "pedt5_2": 3, "pedt5_3": 2, "pedt5_4": 4, "pedt5_5": 4,
        "onset_when": "acquired",
        "baseline_ielt": 1.5,
        "baseline_anxiety": 4,
    })
    result = route(r)
    assert result["variant"] == "A"
    assert "high_anxiety" in result["flags"]


# -----------------------------------------------------------------------------
# Variant B — Hypertonic Pelvic Floor (safety-critical)
# -----------------------------------------------------------------------------

def test_variant_b_clear_hypertonic():
    """4 hypertonic indicators → B, regardless of other signals."""
    r = _base_responses()
    r.update({
        "pedt5_1": 3, "pedt5_2": 3, "pedt5_3": 3, "pedt5_4": 3, "pedt5_5": 3,
        "hyper_1": True, "hyper_2": True, "hyper_3": True, "hyper_5": True,
        "onset_when": "acquired",
        "baseline_ielt": 1.0,
    })
    result = route(r)
    assert result["variant"] == "B"
    assert "no_standard_kegels_initially" in result["flags"]


def test_variant_b_overrides_lifelong():
    """Hypertonic must override the lifelong routing — safety priority."""
    r = _base_responses()
    r.update({
        "pedt5_1": 4, "pedt5_2": 4, "pedt5_3": 4, "pedt5_4": 3, "pedt5_5": 3,
        "hyper_1": True, "hyper_2": True, "hyper_3": True,
        "onset_when": "lifelong",
        "baseline_ielt": 0.5,
    })
    result = route(r)
    assert result["variant"] == "B", "Hypertonic must take priority over lifelong"


def test_variant_b_overrides_porn():
    """Hypertonic must override the porn-conditioned routing."""
    r = _base_responses()
    r.update({
        "pedt5_1": 3, "pedt5_2": 3, "pedt5_3": 3, "pedt5_4": 3, "pedt5_5": 3,
        "hyper_1": True, "hyper_2": True, "hyper_4": True,
        "mast_porn_freq": 5, "mast_grip": 3, "mast_pace": 3, "mast_without_porn": 3,
    })
    result = route(r)
    assert result["variant"] == "B", "Hypertonic must take priority over porn-conditioned"


def test_borderline_hypertonic_stays_below_threshold():
    """Only 2 hypertonic indicators → not B."""
    r = _base_responses()
    r.update({
        "pedt5_1": 3, "pedt5_2": 3, "pedt5_3": 3, "pedt5_4": 3, "pedt5_5": 3,
        "hyper_1": True, "hyper_2": True,  # only 2
        "onset_when": "acquired",
        "baseline_ielt": 1.5,
        "baseline_anxiety": 3,
    })
    result = route(r)
    assert result["variant"] != "B"


# -----------------------------------------------------------------------------
# Variant C — Lifelong / Hypotonic
# -----------------------------------------------------------------------------

def test_variant_c_lifelong_short_ielt():
    """Lifelong + short IELT, no other dominant signals → C."""
    r = _base_responses()
    r.update({
        "pedt5_1": 4, "pedt5_2": 4, "pedt5_3": 4, "pedt5_4": 3, "pedt5_5": 3,
        "onset_when": "lifelong",
        "baseline_ielt": 0.5,
    })
    result = route(r)
    assert result["variant"] == "C"
    assert "consider_pharma" in result["flags"]


def test_lifelong_but_long_ielt_routes_to_a():
    """Lifelong but IELT > 1.5 min should not go to C."""
    r = _base_responses()
    r.update({
        "pedt5_1": 2, "pedt5_2": 2, "pedt5_3": 2, "pedt5_4": 3, "pedt5_5": 2,
        "onset_when": "lifelong",
        "baseline_ielt": 4.0,
    })
    result = route(r)
    assert result["variant"] == "A"


# -----------------------------------------------------------------------------
# Variant D — Porn-Conditioned
# -----------------------------------------------------------------------------

def test_variant_d_classic_pattern():
    """Daily porn + firm grip + fast pace → D, with porn_current flag."""
    r = _base_responses()
    r.update({
        "pedt5_1": 3, "pedt5_2": 3, "pedt5_3": 3, "pedt5_4": 3, "pedt5_5": 2,
        "mast_porn_freq": 4, "mast_grip": 3, "mast_pace": 3, "mast_without_porn": 2,
        "mast_porn_history": "current",
        "onset_when": "acquired",
        "baseline_ielt": 1.5,
    })
    result = route(r)
    assert result["variant"] == "D"
    assert "porn_taper" in result["flags"]
    assert "porn_current" in result["flags"]


def test_porn_use_alone_not_enough():
    """Daily porn but light grip/pace and no dependency → not D."""
    r = _base_responses()
    r.update({
        "pedt5_1": 3, "pedt5_2": 3, "pedt5_3": 3, "pedt5_4": 3, "pedt5_5": 2,
        "mast_porn_freq": 4, "mast_grip": 0, "mast_pace": 0, "mast_without_porn": 0,
        "mast_porn_history": "current",
        "onset_when": "acquired",
        "baseline_ielt": 1.5,
    })
    result = route(r)
    assert result["variant"] != "D"


def test_variant_d_past_heavy_user_with_residual_pattern():
    """
    User stopped heavy porn use over a year ago but retains tight grip / fast pace.
    Currently uses no porn (mast_porn_freq=0). Lifelong-feeling onset because
    PE has been there since adolescence.

    The prior router missed this user — they would have routed to C.
    """
    r = _base_responses()
    r.update({
        "pedt5_1": 3, "pedt5_2": 3, "pedt5_3": 3, "pedt5_4": 3, "pedt5_5": 2,
        "mast_porn_freq": 0,           # Doesn't use porn now
        "mast_grip": 3,                # Habit persists — very firm
        "mast_pace": 3,                # Habit persists — very fast
        "mast_without_porn": 0,        # "Not difficult — I rarely or never use porn anyway"
        "mast_porn_history": "past_stopped",  # KEY: heavy past use
        "onset_when": "lifelong",
        "baseline_ielt": 1.0,
    })
    result = route(r)
    assert result["variant"] == "D", (
        "Past heavy porn user with residual grip/pace patterns must route to D, "
        f"not {result['variant']}. They have the conditioning, just no current use."
    )
    assert "porn_past" in result["flags"]
    assert "porn_taper" not in result["flags"], (
        "Past-stopped users should NOT get porn_taper flag — they don't need a taper."
    )


def test_variant_d_past_recent_quitter_routes_to_d_with_taper_skipped():
    """
    User stopped within the last year. Still gets D routing but no taper module.
    """
    r = _base_responses()
    r.update({
        "pedt5_1": 3, "pedt5_2": 3, "pedt5_3": 3, "pedt5_4": 3, "pedt5_5": 2,
        "mast_porn_freq": 0,
        "mast_grip": 3,
        "mast_pace": 2,
        "mast_porn_history": "past_recent",
        "onset_when": "acquired",
        "baseline_ielt": 1.5,
    })
    result = route(r)
    assert result["variant"] == "D"
    assert "porn_past" in result["flags"]
    assert "porn_taper" not in result["flags"]


def test_past_porn_user_without_residual_pattern_routes_normally():
    """
    User had heavy past use but doesn't have grip/pace conditioning anymore.
    Should route based on other signals — not forced into D just because of history.
    """
    r = _base_responses()
    r.update({
        "pedt5_1": 3, "pedt5_2": 3, "pedt5_3": 3, "pedt5_4": 3, "pedt5_5": 2,
        "mast_porn_freq": 0,
        "mast_grip": 0,           # Light grip — no residual pattern
        "mast_pace": 0,           # Slow pace — no residual pattern
        "mast_porn_history": "past_stopped",
        "onset_when": "acquired",
        "baseline_ielt": 1.5,
        "baseline_anxiety": 4,
    })
    result = route(r)
    assert result["variant"] == "A", (
        "Past user without residual grip/pace patterns should route by other signals."
    )


# -----------------------------------------------------------------------------
# Subclinical advisory
# -----------------------------------------------------------------------------

def test_subclinical_routes_to_a_with_advisory():
    """Low PEDT-5, no other signals → still A but with advisory flag."""
    r = _base_responses()
    r.update({
        "pedt5_1": 1, "pedt5_2": 1, "pedt5_3": 0, "pedt5_4": 1, "pedt5_5": 1,
        "onset_when": "acquired",
        "baseline_ielt": 5.0,
    })
    result = route(r)
    assert result["variant"] == "A"
    assert "subclinical" in result["flags"]


# -----------------------------------------------------------------------------
# Simple runner
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        ("Variant A — classic anxiety-driven", test_variant_a_classic),
        ("Variant B — clear hypertonic", test_variant_b_clear_hypertonic),
        ("Variant B — overrides lifelong (safety)", test_variant_b_overrides_lifelong),
        ("Variant B — overrides porn-conditioned (safety)", test_variant_b_overrides_porn),
        ("Borderline hypertonic stays below threshold", test_borderline_hypertonic_stays_below_threshold),
        ("Variant C — lifelong + short IELT", test_variant_c_lifelong_short_ielt),
        ("Lifelong but long IELT → A", test_lifelong_but_long_ielt_routes_to_a),
        ("Variant D — classic porn-conditioned (current)", test_variant_d_classic_pattern),
        ("Porn use alone not enough → not D", test_porn_use_alone_not_enough),
        ("Variant D — past heavy user with residual pattern", test_variant_d_past_heavy_user_with_residual_pattern),
        ("Variant D — past-recent quitter, taper skipped", test_variant_d_past_recent_quitter_routes_to_d_with_taper_skipped),
        ("Past porn user without residual pattern → A", test_past_porn_user_without_residual_pattern_routes_normally),
        ("Subclinical advisory → A with flag", test_subclinical_routes_to_a_with_advisory),
    ]

    passed = 0
    failed = []
    for name, fn in tests:
        try:
            fn()
            print(f"  ✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {name} — {e}")
            failed.append(name)

    print()
    print(f"{passed}/{len(tests)} tests passed")
    if failed:
        print(f"Failures: {failed}")
        raise SystemExit(1)
