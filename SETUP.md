# Cadence — local setup

This is what to do on your laptop, in order, to get from zero to listening to the pilot.

The whole project is ~50 files: 4 variants × 8 weeks of audio scripts, a Python
diagnostic engine, an audio generation pipeline. Total work to get to the pilot:
about 30 minutes, most of it waiting for `pip install` and the API calls.

## What you need before you start

- A laptop with **Python 3.10 or newer**. Check with `python3 --version`.
- An **ElevenLabs account** with an API key. The Pro plan ($99/mo) has plenty of
  credits for the full project; the Creator plan ($22) covers the pilot easily.
  Get your key at https://elevenlabs.io/app/settings/api-keys.
- About **20 minutes** for setup + pilot generation.
- About **45 minutes** afterwards to listen to the 14 pilot files end-to-end.

---

## Step 1 — Get the project onto your laptop

Unzip `cadence.zip` somewhere you'll remember (e.g., `~/projects/cadence`).

```bash
cd ~/projects/cadence
ls
```

You should see folders `audio/` and `content/`, plus files like `routing.py`,
`questions.json`, `voices.json`, `requirements.txt`, this `SETUP.md`.

If anything's missing, the zip didn't unpack cleanly. Re-extract.

---

## Step 2 — Set up Python

Strongly recommend a virtual environment so this project's dependencies don't
collide with anything else on your machine.

```bash
python3 -m venv .venv
source .venv/bin/activate            # macOS / Linux
# .venv\Scripts\activate             # Windows PowerShell

pip install -r requirements.txt
```

Verify it worked:

```bash
python -c "import elevenlabs; print(elevenlabs.__version__)"
```

You should see a version number like `2.45.0` or higher. If you get
`ModuleNotFoundError`, the venv isn't activated — run the `source` command again.

---

## Step 3 — Add your API key

Copy the template:

```bash
cp .env.example .env
```

Open `.env` in a text editor and replace `sk-paste-your-key-here` with your
actual ElevenLabs API key.

Verify:

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('OK' if os.environ.get('ELEVENLABS_API_KEY','').startswith('sk') else 'NOT FOUND')"
```

Should print `OK`. If `NOT FOUND`, double-check `.env` has no extra spaces or quotes.

> **Important:** `.env` is gitignored. Don't commit it. Don't paste the key into chat.

---

## Step 4 — Verify the project parses cleanly

Before any API calls, sanity-check the content:

```bash
python -m audio.parser
```

Expected output:

```
Parsed 246 audio jobs from /path/to/cadence/content
  Variant A: 62 jobs
  Variant B: 56 jobs
  Variant C: 56 jobs
  Variant D: 72 jobs
  Branched jobs: 41

✓ All parses clean. No duplicate filenames, no missing days.
```

If you see any warnings or the line `⚠ N issues found` — stop and report back.
Something's wrong with the file extraction. Don't try to generate audio yet.

Also run the routing engine tests:

```bash
python test_routing.py
```

Should end with `13/13 tests passed`.

---

## Step 5 — See the cost projection

```bash
python -m audio.estimate
```

This is a no-API-call dry-run. Output is the character count and projected cost.
Confirms the pilot will cost ~$5-10 and the full project ~$220.

---

## Step 6 — Dry-run the pilot

Last sanity check before any real money is spent:

```bash
python -m audio.pilot --dry-run
```

This walks through what the pilot would generate without actually calling
ElevenLabs. You should see 14 lines like:

```
○ [1/7] a_1_1_why-this-works_adam.mp3  (2726 chars, would generate)
```

If you see errors here, stop and report back.

---

## Step 7 — Generate the pilot for real

This is the only step that costs money. ~$5-10 depending on plan, takes about
2-3 minutes total.

```bash
python -m audio.pilot
```

Output will look like:

```
PILOT: 7 sessions × 2 voices = 14 files
Output: /path/to/cadence/audio_output/pilot
...
  → [1/7] a_1_1_why-this-works_adam.mp3
  → [1/7] a_1_1_why-this-works_bella.mp3
  → [2/7] a_1_2_extended-exhale-breathing_adam.mp3
  ...
Generated: 14
```

If a file fails (network blip, rate limit, etc.), the script retries automatically.
If retries don't fix it, just re-run `python -m audio.pilot` — completed files are
skipped, only failed ones get retried.

When done, `audio_output/pilot/` contains 14 MP3s plus a `LISTENING_CHECKLIST.txt`.

---

## Step 8 — Listen

Open `audio_output/pilot/LISTENING_CHECKLIST.txt` in any text editor. It walks
through what to evaluate.

The order I recommend listening:

1. **Day 1 Adam** — the user's first impression. Does the voice land?
2. **Day 1 Bella** — same script, different voice. Compare.
3. **Day 2 Adam** — the breath-heavy session. Are the breath cues followable?
4. **Day 4 Adam** — the "Spectatoring" session, more emotionally weighted.
5. **Day 5 Adam** — has a 120s pause baked in (the body-scan finalizer); see
   how the chained `<break>` tags actually sound. This informs whether we need
   to handle long pauses out-of-band for production.
6. The remaining 8 — skim, mostly looking for systematic issues you've already
   identified, not session-by-session evaluation.

Make notes as you go. The categories that matter for the next decision:

- **Pacing** — too fast, too slow, or right
- **Tone** — does it match the "calm, measured, warm but not soft" direction
- **Breath cues** — are the durations right for actual paced breathing
- **Pronunciation** — any words consistently mangled (esp. "Kegel," "diaphragmatic," "IELT")
- **Artifacts** — clicks, speed-ups, glitches, voice drift mid-session
- **Voice choice** — Adam vs Bella vs both as user choice

---

## What to report back

When you come back to chat, tell me:

1. **Did setup work cleanly?** Any step where the verification command failed.
2. **Pilot output quality.** Honest read on each of the five categories above.
3. **Voice settings decision.** Are stability=0.55, similarity=0.75, style=0.15
   producing what you want, or do we need to retune? (For long-form narration the
   trade-off is: higher stability = more consistent but flatter, lower stability =
   more expressive but can drift character mid-session.)
4. **Adam vs Bella decision.** Ship both as user choice, or pick one?
5. **Long pauses.** How did Day 5's 120s pause sound? Acceptable, or do we need to
   build the audio-splitting machinery before scaling production?
6. **Any sessions that need re-writing.** Some content reads well on paper but
   sounds awkward voiced. Note specific moments — I'll edit the scripts before
   we generate the rest.
7. **Pronunciation overrides needed.** List any words that came out wrong.

If everything sounds good, the next step is `python -m audio.generate --all`
to produce all 492 files (~$220, ~30 minutes of API calls).

If things need adjustment, we adjust in chat and you re-run the pilot before scaling.

---

## Project structure reference

```
cadence/
├── SETUP.md                          ← you are here
├── README.md                         ← project overview
├── requirements.txt                  ← Python dependencies
├── .env.example                      ← template for your API key file
├── .gitignore                        ← keeps secrets/audio out of git
│
├── questions.json                    ← diagnostic intake schema
├── voices.json                       ← Adam + Bella voice IDs and settings
├── routing.py                        ← diagnostic → variant routing engine
├── test_routing.py                   ← 13 tests for the routing logic
├── cli.py                            ← interactive CLI for testing routing
│
├── content/                          ← all audio scripts (~104k words)
│   ├── _pacing_model.md             ← Standard/Intensive/Extended pacing
│   ├── _tracker.md                   ← session-by-session production tracker
│   ├── variant_a_week_1.md          ← Anxiety-Driven Acquired profile
│   ├── variant_a_week_2.md
│   ├── ...                           ← (all 4 variants × 8 weeks)
│   └── shared_*.md                   ← shared modules (breath, edging, etc.)
│
├── audio/                            ← production pipeline
│   ├── README.md                     ← pipeline-specific docs
│   ├── parser.py                     ← markdown → AudioJob records
│   ├── render.py                     ← script → ElevenLabs SSML text
│   ├── estimate.py                   ← cost projection
│   ├── generate.py                   ← actual API calls
│   └── pilot.py                      ← Variant A week 1 pilot batch
│
├── qa_variant_a.md                   ← QA findings, all applied
├── qa_variants_bcd.md                ← QA findings for B/C/D, all applied
│
└── audio_output/                     ← generated MP3s land here (gitignored)
    └── pilot/                        ← pilot batch output
        ├── LISTENING_CHECKLIST.txt
        └── *.mp3                     ← 14 files
```

---

## If something breaks

- **`ModuleNotFoundError: No module named 'elevenlabs'`** — the venv isn't activated.
  Run `source .venv/bin/activate` again, or re-run `pip install -r requirements.txt`.
- **`ELEVENLABS_API_KEY not set`** — the `.env` file isn't being read. Check it's
  named exactly `.env` (no `.txt` extension), it's in the project root, and the
  key starts with `sk`.
- **`401 Unauthorized`** — API key is wrong or revoked. Generate a new one.
- **`429 Too Many Requests`** — rate limit. Wait a minute, re-run; the script
  is resumable.
- **`Insufficient credits`** — top up your ElevenLabs account or upgrade plan.
- **The pilot generates but audio sounds bad** — that's the whole point of the pilot.
  Note specifics, report back, we adjust before scaling.

When in doubt, just paste the error back to chat. I'll diagnose.
