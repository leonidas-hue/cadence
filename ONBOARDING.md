# Cadence — week-long onboarding test

This is the test harness for your week-1 self-evaluation. You'll run the
diagnostic, get routed, the script generates week-1 audio for your variant,
and you get an HTML page you can open in any browser.

Assumes you've already done the basic setup from `SETUP.md` (Python venv,
dependencies installed, `.env` with your ElevenLabs API key, pilot run successful).

## Drop the new file in

Place `onboarding.py` at the root of your cadence/ project, next to `cli.py`.

```
cadence/
├── onboarding.py     ← new
├── cli.py
├── routing.py
├── questions.json
└── ...
```

## Run it

```bash
# Activate your venv if it isn't already
source .venv/bin/activate

# Run the harness
python onboarding.py
```

The script will:

1. **Run the diagnostic interactively.** ~3-5 minutes. Answer honestly — you'll
   route to whatever variant fits your actual profile.
2. **Save your diagnostic result** to `state/diagnostic.json`. This is just a
   plain JSON file you can inspect or delete.
3. **Generate week-1 audio** for your routed variant, both Adam and Bella voices.
   ~10-15 MP3s depending on variant. Costs ~$5-7. Skipped if files already exist.
4. **Build a static HTML page** (`onboarding.html`) listing the week with
   embedded audio players.

When it's done, open `onboarding.html` in any browser (double-click the file,
or use `open onboarding.html` on macOS / `start onboarding.html` on Windows).

## What the HTML gives you

- Your variant assignment at the top, with flags and reasoning
- A radio-button toggle to listen Adam-only / Bella-only / both side-by-side
- All 7 days of week 1, with today's session visually highlighted
- Past days dim out, future days stay visible (so you don't lose your place)
- Each session has both voice players inline — no clicking through files

The HTML is fully self-contained and references the audio files by relative
path. As long as `audio_output/onboarding/` lives next to `onboarding.html`,
the players will work.

## During the week

Each morning, run:

```bash
python onboarding.py --rebuild-html
```

This re-reads your saved state and rebuilds the HTML so the "today"
highlighting moves to the right day. Doesn't regenerate audio or re-run the
diagnostic. Takes about 2 seconds.

## Resetting

If you want to start over with a different variant (e.g., you answered the
diagnostic in one direction and want to test another):

```bash
python onboarding.py --reset      # deletes state and HTML
python onboarding.py              # diagnostic again from scratch
```

If you just want to re-generate the audio without redoing the diagnostic:

```bash
# Delete the audio files for your variant, then:
python onboarding.py              # it'll skip the diagnostic (existing state)
                                  # and regenerate just the missing audio
```

## Flags and options

| Flag | What it does |
|---|---|
| (none) | Full flow: diagnostic → audio → HTML |
| `--rebuild-html` | Rebuild HTML from saved state only (no audio, no diagnostic) |
| `--reset` | Delete saved state and HTML, start clean |
| `--dry-run` | Run diagnostic + build HTML but skip ElevenLabs API calls |
| `--skip-audio` | Run diagnostic + build HTML, skip audio generation |

## Known limitations

**Variant D Week 1 branching.** If you route to Variant D, the parser doesn't
currently split Day 1 and Day 5 into separate `current` and `past` versions
(the markdown formatting in week 1 differs from later weeks). You'll get
merged content for those two days. Acceptable for a one-week test; we'll
fix the parser before full production.

**Audio quality.** The HTML page has a banner reminding you that this is
unrefined pilot output. Focus on protocol fit (does this make sense as a
daily program?) and tone direction (does the voice character match what we
want?), not surface polish — those issues are on the fix list for after your
week-test results come back.

## What to track during the week

- Did the diagnostic feel like it captured your actual situation?
- Was the routed variant the one you expected? If not, what did it miss?
- For each daily session: did it make sense at this point in the protocol?
  Did the duration feel right? Did anything land badly?
- Any sessions you wanted to skip — and why?
- Any sessions you wanted to repeat?
- Pronunciation problems beyond what you've already noted
- Any moments where the audio direction felt off (rushed, robotic,
  performative, etc.)

When you come back to chat, paste your notes. The audio quality refinement
pass and any script edits will be informed by what you actually experienced
across the week, not just first-impression spot checks.
