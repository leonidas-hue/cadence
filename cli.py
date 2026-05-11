"""
Cadence — Interactive CLI

Loads questions.json, runs the user through the diagnostic, routes them
to a protocol variant, then asks variant-specific preferences for
optional add-ons. Outputs the final personalized plan summary.

Usage:
    python cli.py
"""

import json
import sys
from pathlib import Path

from routing import route, format_result


QUESTIONS_PATH = Path(__file__).parent / "questions.json"


# -----------------------------------------------------------------------------
# Rendering helpers
# -----------------------------------------------------------------------------

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
        for line in _wrap(section["description"], 68):
            print(f"  {line}")
    print()


# -----------------------------------------------------------------------------
# Question askers
# -----------------------------------------------------------------------------

def _ask_single_select(q: dict) -> object:
    print()
    for line in _wrap(q["text"], 68):
        print(f"  {line}")
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
    for line in _wrap(q["text"], 68):
        print(f"  {line}")
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


# -----------------------------------------------------------------------------
# Final plan assembly
# -----------------------------------------------------------------------------

def _core_components_for_variant(variant: str) -> list[str]:
    if variant == "A":
        return [
            "Breathwork & parasympathetic activation",
            "Cognitive restructuring (CBT) audio lessons",
            "Sensate-focus principles",
            "Light pelvic floor maintenance",
        ]
    if variant == "B":
        return [
            "Pelvic floor RELAXATION (reverse Kegels)",
            "Diaphragmatic breathing",
            "Hip mobility & stretching",
            "Standard Kegels NOT included initially — would worsen your profile",
        ]
    if variant == "C":
        return [
            "Progressive pelvic floor strengthening",
            "Stop-start / edging practice",
            "Reverse Kegels (added week 5)",
            "Educational track on pharma bridge options",
        ]
    if variant == "D":
        return [
            "Masturbation reconditioning (grip / pace / stimulus)",
            "Porn taper protocol",
            "Edging without visual stimulus",
            "Solo sensate-focus work",
        ]
    return []


def _format_plan(result: dict, prefs: dict) -> str:
    lines = []
    lines.append("")
    lines.append(_hr("═"))
    lines.append("  YOUR PERSONALIZED PROTOCOL")
    lines.append(_hr("═"))
    lines.append("")
    lines.append(f"  Track: Variant {result['variant']} — {result['name']}")
    lines.append(f"  Daily commitment: {prefs.get('session_time', 10)} minutes")
    lines.append("")

    lines.append("  CORE PROTOCOL (recommended, daily):")
    for component in _core_components_for_variant(result["variant"]):
        lines.append(f"    • {component}")
    lines.append("")

    addons = []
    if prefs.get("addon_pelvic") == "yes":
        addons.append("Supplementary pelvic floor training (2-3 sessions/week)")
    if prefs.get("addon_breathwork") == "yes":
        addons.append("Extra breathwork sessions")
    if prefs.get("addon_mindfulness") == "yes":
        addons.append("Daily mindfulness (5-10 min)")
    if addons:
        lines.append("  ADD-ONS YOU CHOSE:")
        for a in addons:
            lines.append(f"    + {a}")
        lines.append("")
    else:
        lines.append("  No optional add-ons. You can change this anytime in settings.")
        lines.append("")

    if "recommend_pt" in result["flags"]:
        lines.append("  ⚠ STRONG RECOMMENDATION:")
        lines.append("    Pelvic floor physiotherapy alongside this program.")
        lines.append("    Cadence supplements in-person care for your profile.")
        lines.append("")

    if "consider_pharma" in result["flags"]:
        lines.append("  NOTE:")
        lines.append("    Pharma options (dapoxetine, topical lidocaine) are covered")
        lines.append("    in your educational track as a legitimate bridge while you")
        lines.append("    build behavioral skills. Consult a doctor for prescriptions.")
        lines.append("")

    if "subclinical" in result["flags"]:
        lines.append("  NOTE:")
        lines.append("    Your screening score doesn't indicate clinically significant PE.")
        lines.append("    The program will still work if you want greater control or")
        lines.append("    presence — but it's optional for your profile.")
        lines.append("")

    lines.append(_hr("═"))
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Main flow
# -----------------------------------------------------------------------------

def run() -> None:
    with open(QUESTIONS_PATH) as f:
        schema = json.load(f)

    print()
    print(_hr("═"))
    print("  CADENCE — Endurance & Control Training")
    print("  Diagnostic Intake (v" + schema["version"] + ")")
    print(_hr("═"))
    print()
    print("  This intake takes 3-5 minutes and routes you to one of four")
    print("  evidence-based protocols. Your answers stay on this device.")
    print()
    print("  Press Enter to begin.")
    input()

    diagnostic_sections = [
        s for s in schema["sections"]
        if not s.get("show_after_routing", False)
    ]
    preferences_sections = [
        s for s in schema["sections"]
        if s.get("show_after_routing", False)
    ]

    responses: dict[str, object] = {}

    for section in diagnostic_sections:
        _print_section_header(section)
        for q in section["questions"]:
            responses[q["id"]] = _ask(q)

    # Route the user
    result = route(responses)
    variant = result["variant"]

    # Show variant assignment first
    print()
    print()
    print(format_result(result))
    print()

    # Variant-filtered preferences
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

    print(_format_plan(result, prefs))
    print()
    print("  In the full app, you'd now move into your first daily session.")
    print()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n\n  Cancelled.\n")
        sys.exit(0)
