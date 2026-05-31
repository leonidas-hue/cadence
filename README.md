# Cadence

App-only training program for premature ejaculation. Evidence-based, four-variant
diagnostic routing, ~104,000 words of audio scripts, no hardware, one-time pricing.

## Project state

| Phase | Status |
|---|---|
| Phase 1 — Diagnostic + routing engine | ✅ Complete (13 tests passing) |
| Phase 2 — Content scripting | ✅ Complete (4 variants × 8 weeks, ~246 sessions) |
| QA pass (5-pass review) | ✅ Complete (Variants A/B/C/D, all priorities applied) |
| Phase 2.5 — Audio production pipeline | ✅ Pilot generated & validated; Variant A weeks 1–5 rendered (83 MP3s) |
| Phase 3 — Flutter app scaffold | ⏸ Pending pilot validation |
| Phase 4 — Practice modes | ⏸ |
| Phase 5 — Logging + progress | ⏸ |
| Phase 6 — Privacy + payments | ⏸ |
| Phase 7 — Closed beta | ⏸ |
| Phase 8 — Public launch | ⏸ |

## Where to start

If you've never run this locally before: read **`SETUP.md`**. It walks you from
fresh laptop to listening to the audio pilot in about 30 minutes.

If you're already set up, the most useful commands are:

```bash
python -m audio.parser     # validate all 246 session scripts parse cleanly
python -m audio.estimate   # cost projection for full audio production
python -m audio.pilot      # generate the validation batch (Variant A week 1)
python test_routing.py     # 13 routing-engine tests
python cli.py              # interactive intake (manually try the routing)
python onboarding.py       # full onboarding test: diagnostic → audio → HTML page
```

The onboarding harness runs you through the diagnostic, routes you to a variant,
generates week-1 audio, and builds a static HTML page with embedded players.
See **`ONBOARDING.md`** for full usage and flags (`--rebuild-html`, `--reset`,
`--dry-run`, `--skip-audio`).

## The four variants

The diagnostic at intake routes users into one of four protocols, with a strict
priority order that ensures hypertonic users (where standard Kegels would harm)
are caught first:

- **Variant B — Hypertonic Pelvic Floor** *(safety-critical, evaluated first)*
  Reverse Kegels + diaphragmatic breath + hip mobility. Recommends pelvic-floor PT.
  No standard Kegels anywhere.
- **Variant D — Porn-Conditioned**
  Branches at week 4-5 between current users (porn taper) and past users
  (solo-to-partnered transfer). Grip / pace / stimulus recalibration.
- **Variant C — Lifelong / Hypotonic**
  Standard Kegel building, longer 8-12 week timeline, week-5 pharma educational
  module covering dapoxetine and topical lidocaine.
- **Variant A — Anxiety-Driven Acquired** *(default)*
  Three-way branching at week 3 (partnered-yes / partnered-declined / solo).
  Anxiety regulation, stop-start, sensate focus.

Routing logic lives in `routing.py`. Diagnostic schema in `questions.json`.
Test cases covering the priority ordering and edge cases in `test_routing.py`.

## What's in this repo

```
cadence/
├── SETUP.md                    ← read this first if you're setting up
├── README.md                   ← you are here
├── requirements.txt            ← Python deps (elevenlabs, python-dotenv)
├── .env.example                ← API key template
│
├── content/                    ← all audio scripts, organized by variant × week
├── audio/                      ← production pipeline (parser, render, generate, pilot)
│
├── routing.py                  ← diagnostic → variant assignment
├── questions.json              ← intake questionnaire schema
├── voices.json                 ← ElevenLabs voice IDs and settings
├── test_routing.py             ← 13 tests
├── cli.py                      ← interactive routing CLI
├── onboarding.py               ← week-1 test harness (diagnostic + audio + HTML)
│
├── qa_variant_a.md             ← QA findings doc, all priorities applied
└── qa_variants_bcd.md          ← QA findings doc, all priorities applied
```

## Tech stack (committed)

- Flutter + Drift/SQLite + Riverpod + just_audio + RevenueCat
- ElevenLabs Multilingual v2 for TTS
  - Adam: `s3TPKV1kjDlVtZbl4Ksh`
  - Bella: `4RZ84U1b4WCqpu57LvIq`
- Local-first, no backend in v1
- MIT licensed, solo-built
- One-time pricing target ~€29-39 lifetime; free tier = diagnostic + week 1

## Working with this project

The routing logic, content, and audio pipeline are fully self-contained. Anyone
familiar with Python can run, test, and modify them. The Flutter app build phase
will reuse `questions.json` and `voices.json` as data files; the routing logic
will need to be ported to Dart (~1-2 hour job).

Audio scripts are the source of truth — generated MP3s are derived artifacts,
gitignored. To change a session, edit the markdown, then regenerate that file
with `python -m audio.generate`.

For a full session-by-session production tracker, see `content/_tracker.md`.
For design notes on pacing variations (Standard / Intensive / Extended),
see `content/_pacing_model.md`.
