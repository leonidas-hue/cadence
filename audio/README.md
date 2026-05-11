# Cadence audio pipeline

End-to-end production pipeline for generating ~246 MP3s × 2 voices = 492 audio files
from the markdown scripts in `content/`.

## Pipeline overview

```
content/*.md
    │
    ▼
parser.py     →  extracts AudioJob records (one per session, branched where applicable)
    │
    ▼
render.py     →  converts script body to ElevenLabs-ready text with SSML break tags
    │
    ▼
generate.py   →  calls ElevenLabs API, writes MP3s to audio_output/
    │
    ▼
pilot.py      →  the small validation batch: Variant A week 1, both voices
estimate.py   →  cost projection across all jobs and plans
```

## Quick start

```bash
# 1. Install dependencies
pip install elevenlabs python-dotenv

# 2. Set your ElevenLabs API key
export ELEVENLABS_API_KEY=sk-your-key-here
# OR put it in a .env file at repo root: ELEVENLABS_API_KEY=sk-...

# 3. Verify all content parses cleanly (no API calls, instant)
python -m audio.parser

# 4. See the cost projection (no API calls)
python -m audio.estimate

# 5. Dry-run the pilot (no API calls)
python -m audio.pilot --dry-run

# 6. Run the actual pilot (~$5-10, 14 files, takes a few minutes)
python -m audio.pilot

# 7. Listen to all 14 files end-to-end with the listening checklist.
#    The checklist is written to audio_output/pilot/LISTENING_CHECKLIST.txt

# 8. After validation, full production:
python -m audio.generate --all
```

## Numbers

As of the most recent parser run:

- **246 audio jobs total** across the four variants
  - Variant A: 62 jobs (56 days, but week 3 has 3-way branching for days 18-20)
  - Variant B: 56 jobs
  - Variant C: 56 jobs
  - Variant D: 72 jobs (56 days, but weeks 4-5 are dual-branched + days 36/49)
- **41 branched jobs** — Variant A week 3 has p/s/n branches; Variant D has current/past
- **~559k characters single-voice**, **~1.12M characters two-voice**
- **Projected cost** (Pro plan @ $99/mo, ~$0.0002/char): ~$220 for full two-voice production

## Files in this directory

| File | Purpose |
|---|---|
| `parser.py` | Markdown → AudioJob records. Run as script to validate parsing. |
| `render.py` | AudioJob.body_md → ElevenLabs-ready text. Translates `[PAUSE Xs]` to SSML. |
| `estimate.py` | Total characters and cost projection across plans. |
| `generate.py` | Calls the API. Resumable (skips files that already exist). |
| `pilot.py` | The small validation batch. Run this before the full production. |
| `__init__.py` | Package marker + module documentation. |

## Decisions baked into the pipeline

These were judgment calls during pipeline construction. Worth knowing so you can
adjust if any of them turn out wrong.

### Model: `eleven_multilingual_v2`

Reasoning: ElevenLabs offers v3 (newest, most expressive), v2 (most stable), and Flash
(lowest latency). For Cadence:

- v3 is officially marked "is currently in alpha and is subject to change" in the API
  docs, with a recommendation to "consider generating several generations and allowing
  the user to select the best one." That's the wrong shape for a 246-script production
  pipeline where consistency matters more than emotional range.
- Flash sacrifices quality for latency, which we don't need (this isn't real-time).
- Multilingual v2 is the "consistent, predictable neutral narration" model. The
  current community consensus (early 2026) is that v2 is the right pick when the
  priority is stable long-form output.

If voice quality concerns surface during the pilot, v3 is a one-line config change.

### Pause handling: SSML `<break>` chained for >3s

ElevenLabs v2 supports `<break time="X.0s"/>` tags up to 3 seconds. The renderer:

- Pauses ≤3s → single `<break>` tag of that duration
- Pauses 4-9s → chained breaks (a 5s pause becomes `<break time="3.0s"/> <break time="2.0s"/>`)
- Pauses ≥10s → flagged as "long pauses." The renderer still emits a single 3s break
  but warns that for production these should be handled by splitting the audio at
  the long-pause point and letting the app insert real silence.

23 sessions in the library have pauses ≥30s (silent meditation, body scan finalizers).
Recommended approach: in the app, the audio engine renders the session in chunks
separated by these long pauses, with an `AudioController` inserting actual silence.
This is a v2 build-out — for the pilot, accept the chained-break approximation.

### Dropped: tone markers `[soft]` and `[firmer]`

Multilingual v2 does not reliably honor inline emotion control. The tone direction
is communicated to the model through:
- voice settings (`stability`, `similarity_boost`, `style`)
- the writing itself (sentence length, punctuation, line breaks)
- voice selection (Adam reads firmer than Bella in the same script)

Tone markers in the script are dropped at render time. They're useful for human
voice talent and would be useful for v3's audio tag system (`[whispered]`, `[firmer]`),
but they confuse v2 when left inline.

### Output format: `mp3_44100_128`

44.1 kHz mono 128 kbps MP3. As committed in the original spec.

### Voice settings: stability 0.55 / similarity 0.75 / style 0.15

From `voices.json`. These produce moderately consistent output with some prosody
variation — appropriate for instructional/calm narration. If during pilot listening
the voice drifts character mid-session, raise stability to 0.65-0.70. If it sounds
too monotone, lower style to 0.10 or stability to 0.45.

### Default rate limit: 0.5s between calls

Conservative — ElevenLabs allows higher on most plans. For 492 files this means
a full production run takes ~4-5 minutes plus generation latency, which is fine
for an overnight job. Raise to 0.2s or remove if you're confident in your rate limit.

## Resumability

`generate.py` checks `output_path.exists()` before generating. If a session has
already been written, it's skipped. So:

- If a run fails partway through, just re-run — it picks up where it left off.
- If you need to re-generate a specific session (e.g., after a script edit),
  delete that one MP3 and re-run.
- For an entire variant, delete the relevant filenames and re-run.

## What this pipeline does NOT do

- **Mixing/mastering.** The MP3s come out as TTS output. If you want consistent
  loudness across files, run them through `ffmpeg-normalize` or similar after generation.
- **Long-pause splitting.** The 23 sessions with pauses ≥30s should be split into
  multiple audio chunks for the app to play with real silence between them. The
  pipeline currently emits a single MP3 with a 3-second break in place of the long
  pause — workable for pilot, suboptimal for production.
- **Pronunciation overrides.** If a word is consistently mispronounced by the model
  (likely candidates: "Kegel," "diaphragmatic"), the only fix on v2 is text substitution
  in the source script. Phoneme tags only work on Flash v2 / English v1.
- **A/B testing voice settings.** If you want to compare stability=0.55 vs 0.70 on the
  same session, you'll need to call `generate_one()` directly with custom config.
- **Audio QA.** No automated check for "did this MP3 actually contain coherent speech."
  Manual listening is required.

## Listening checklist

When the pilot completes, `audio_output/pilot/LISTENING_CHECKLIST.txt` will contain
the full checklist. Summary:

- Pacing — does the voice rush, or stay measured?
- Tone — calm/grounded vs wellness-influencer/clinical-cold
- Breath cues — durations match natural breathing
- Pronunciation — flag any consistent mispronunciations
- Artifacts — clicks, speed-ups, glitches around dense break tags
- Long pauses — Day 2 has a 90s pause, Day 5 has a 120s pause; check those specifically

## Common issues

**`elevenlabs SDK not installed`**
→ `pip install elevenlabs python-dotenv`

**`ELEVENLABS_API_KEY not set`**
→ `export ELEVENLABS_API_KEY=sk-...` or add to a `.env` file at repo root.

**Rate-limit errors (429)**
→ Increase `DELAY_BETWEEN_CALLS` in `generate.py`. Default 0.5s should be safe on most plans.

**Voice drifts character mid-session**
→ Raise `stability` in `voices.json` from 0.55 to 0.65-0.70.

**Voice sounds too monotone**
→ Lower `stability` to 0.45 or `style` to 0.10. Trade-off: more variation, sometimes drift.

**A specific session has audio artifacts around dense breath cues**
→ The renderer warns when a session has >80 break tags. Either split that session
into two parts at a natural break, or reduce the breath cue density in the script.

**A long pause (>10s) plays as a short pause**
→ Expected. Long pauses currently render as a 3s break with a renderer warning.
For production, split the audio at that point and let the app insert real silence.

## Future work

When the pilot is validated and full production proceeds:

1. **Splice silence at long-pause boundaries.** The 23 sessions with ≥30s pauses
   should be rendered as N+1 audio files (one per inter-pause segment), with the app
   inserting silence between them.
2. **Loudness normalization.** Run all output through `ffmpeg-normalize -nt ebu -t -16`
   so volume is consistent across sessions and devices.
3. **Pronunciation audit.** Spot-check 5-10% of files for any consistent mispronunciation.
   Apply text substitution for terms that misfire.
4. **A/B voice settings on emotionally heavier sessions.** Day 4 (Spectatoring) and the
   week-7 partner-conversation sessions may benefit from slightly different voice settings.
   Test once before locking in.
