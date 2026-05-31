# SKILL.md — Cadence audio scripts for ElevenLabs

This is the canonical script-writing guide for the Cadence project. Read this before writing or editing any content file in `content/`.

It synthesizes:
- ElevenLabs official best practices (https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices)
- Empirical findings from this project's audio generation work

**Live docs:** ElevenLabs publishes machine-readable docs at `https://elevenlabs.io/docs/llms-full.txt`. Append `.md` to any docs page URL for the markdown version. There's also an MCP server at `https://elevenlabs.io/docs/_mcp/server` that Claude Code can connect to for live documentation queries.

---

## 1. Model and constraints we work within

**Model:** `eleven_multilingual_v2`. Chosen for stable, consistent long-form narration. NOT v3 (alpha, non-deterministic).

**Per-request limit:** 10,000 characters max. Our longest session is ~5,000, so well under.

**Pricing:** 1 credit per character of input. ~$0.0002/char on Pro tier (Pro = 500k credits/mo for $99). A typical 8-min session is ~3,000 chars → ~$0.60 per voice → ~$1.20 for Adam + Bella.

**What v2 cannot do:**
- Honor `[soft]` / `[firmer]` / `[whispered]` tone markers inline (those are v3 audio tags)
- Honor SSML `<phoneme>` tags (Flash v2 / English v1 only)
- Honor markdown italics (`*word*`) — stripped to plain text, no emphasis
- Pause at blank lines / paragraph breaks (whitespace is collapsed)

**What v2 can do reliably:**
- `<break time="X.Xs"/>` tags up to 3 seconds
- Natural punctuation pauses (periods, commas, em-dashes, ellipses)
- Number normalization (`$1,000,000` → "one million dollars")
- Pronunciation dictionaries via `.pls` files (alias substitutions for problem words)
- Stable voice character across long sessions when stability ≥ 0.55

---

## 2. The pause economy (most important section)

ElevenLabs explicitly warns: *"Using too many break tags in a single generation can cause instability. The AI might speed up, or introduce additional noises or audio artifacts."*

This warning is real. We saw it manifest in the library audio: a 5-minute breath script with 18 break tags packed in 30 seconds of narration compressed to ~30 seconds total playback. **Break tags are not free.**

### The hierarchy of pauses (use in this order)

| Pause length needed | Tool | When |
|---|---|---|
| ~300ms (sentence boundary) | Period (`.`) | Default. Always there from normal grammar. |
| ~400ms (short beat mid-sentence) | Em-dash (`—`) | Replacing some commas where you want an actual pause |
| ~600ms (hesitant/reflective) | Ellipsis (`…`) | Reflection moments, deliberate trailing thoughts |
| 1s (between thought groups) | `[PAUSE 1s]` | Between substantive sentences in what was conceptually one paragraph |
| 2s (between topics) | `[PAUSE 2s]` | Between distinct paragraphs / topic shifts |
| 3s (section break) | `[PAUSE 3s]` | Strong shift in what the listener is doing or focusing on |
| 5s+ (reflection moment) | `[PAUSE 5s]` | The listener is meant to think; you're holding silence on purpose |
| 10s+ (long silent practice) | **DO NOT use chained `<break>` tags** | App-side concern: split audio at this point, insert real silence |

### The rule

**Prefer punctuation pauses over `<break>` tags wherever possible.** Em-dashes and ellipses cost zero break-tag budget but still produce real pauses (per the official docs, *"these are less consistent"* than break tags but they work).

Reserve `[PAUSE Xs]` markers for pauses ≥1 second. For shorter beats, use punctuation.

### Density caps (empirical, from observed failures)

The risk isn't total break-tag count — it's **chained back-to-back breaks**. The library audio failure happened because long pauses like `[PAUSE 30s]` got rendered as chains of 10+ break tags packed together, with very little spoken content between them. Single break tags spread across substantive narration are safe even at high totals.

| Pattern | Risk level |
|---|---|
| Single `<break>` tags between substantive sentences | Safe, even at 40+ per session |
| Chains of 2-3 break tags (e.g. `[PAUSE 5s]` → 2 breaks) | Low risk, used for natural multi-second pauses |
| Chains of 4+ break tags in close succession | **Compression risk** — model starts ignoring break durations |
| Break tags packed into short spans of narration (high tags-per-word) | **Compression risk** — same as above |

The library audio failure had **0.10-0.26 tags-per-word ratio** with most breaks chained. The Week 1 Variant A scripts after editing have 0.05-0.12 tags-per-word ratio but **with zero chained breaks** (all singletons), so they're safe.

Rule of thumb: if your session has more than ~5 `[PAUSE]` markers of duration ≥10s, the renderer will produce chained breaks that risk artifacts. Restructure those long pauses (split into multiple audio segments with real silence between) rather than chaining `<break>` tags.

---

## 3. Paragraph density (the "starts too quickly" problem)

Paragraphs with 4+ substantive sentences read as a rapid continuous rush. The blank lines in markdown produce no pause; only the period's natural ~300ms beat separates the sentences.

**Substantive sentence** = one that introduces or develops an idea.
> *"Your inhale is sympathetic — it speeds the heart up."*

**Non-substantive sentence** = a short coupled phrase that flows into the next.
> *"Drop them. Let them be heavy."*

### What to do with dense paragraphs

For any paragraph with 4+ substantive sentences, insert `[PAUSE 1s]` between thought groups. Worked example:

**Before** (one paragraph, 6 sentences):
> The body has two states that matter here. The first is sympathetic — that's your fight-or-flight system. Heart rate up, breathing fast and shallow, muscles tense, attention narrow. This is the state that triggers ejaculation quickly. It's evolutionarily efficient. It's also the opposite of what you want during sex.

**After**:
> The body has two states that matter here.
>
> [PAUSE 1s]
>
> The first is sympathetic — that's your fight-or-flight system. Heart rate up, breathing fast and shallow, muscles tense, attention narrow.
>
> [PAUSE 1s]
>
> This is the state that triggers ejaculation quickly. It's evolutionarily efficient.
>
> [PAUSE 1s]
>
> It's also the opposite of what you want during sex.

### What does NOT need extra pauses

- **Rapid-fire body scan cues** ("The shoulders. Notice if they're pulled up. Drop them.") — the staccato IS the point
- **Intentional overwhelm passages** (e.g. spectatoring questions cascade) — rapid-fire IS the experience being described
- **Short coupled imperatives** ("Drop them. Let them be heavy.") — one beat, leave alone
- **Breath cycle markers** — `[INHALE] / [EXHALE]` have their own rhythm

---

## 4. Pronunciation

### What works in Multilingual v2

- **Numbers as digits** are fine for currency, simple integers, and dates. v2 normalizes them. *"$1,000,000" → "one million dollars"*
- **Numbers as digits FAIL** for phone numbers, IDs, IELTs (without context). Spell those out: `"one two three"` not `"123"`.
- **Common abbreviations** are recognized (`"Dr."` → "Doctor", `"St."` → "Street")
- **All-caps acronyms** typically read letter-by-letter (`"PE"` → "P-E", `"IELT"` → "I-E-L-T")

### What we've seen mispronounced (Cadence-specific)

| Term | Risk | Fix |
|---|---|---|
| Kegel | "Keg-ull" instead of "Kay-gull" | Alias: `<grapheme>Kegel</grapheme><alias>Kay-gull</alias>` |
| IELT | Letter-by-letter usually, but inconsistent | Spell out: "I.E.L.T." or write as "I E L T" in script |
| PE | Risk of "pee" | Confirmed reads as "P-E" most of the time; if "pee" happens, alias |
| Diaphragmatic | Sometimes stresses wrong syllable | Listen and judge; if wrong, alias |

### The pronunciation dictionary approach

For terms that consistently mispronounce, build a `pronunciation.pls` file at the project root:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lexicon version="1.0"
  xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"
  xsi:schemaLocation="..."
  alphabet="cmu-arpabet" xml:lang="en-GB">

  <lexeme>
    <grapheme>Kegel</grapheme>
    <alias>Kay-gull</alias>
  </lexeme>

  <lexeme>
    <grapheme>IELT</grapheme>
    <alias>I E L T</alias>
  </lexeme>
</lexicon>
```

Upload via the ElevenLabs project settings. Or apply via text-substitution in the renderer (`audio/render.py`) at generation time — slightly hacky but doesn't require touching the source scripts.

**Pronunciation dictionaries are case-sensitive.** "kegel" vs "Kegel" are different entries.

---

## 5. Emphasis and emotion

v2 cannot honor `[soft]` / `[firmer]` / italics. Three ways to add emphasis that DO work:

### Capitalization for stress

Per official docs: *"capitalization signals emphasis."* Use sparingly.

> *"You don't have to be perfect. You just have to keep showing UP."*

### Narrative tagging (limited usefulness for instructional content)

For dialogue/narrative content, embed pacing cues in narration:

> *"'I'm not sure,' he said slowly."*

The "slowly" cues the model. **Not really applicable to Cadence** since we don't have characters speaking, but worth knowing.

### Punctuation for emphasis

- Em-dashes (`—`) for parenthetical emphasis: *"And — surprisingly — it works."*
- Ellipses (`…`) for hesitation or thought: *"That's the foundation… every day, week after week."*
- Exclamation marks rarely (we're calm, not enthusiastic)

### What does NOT work

- `*italics*` — markup gets stripped, words read flat
- Bold `**text**` — same
- `[soft]` / `[firmer]` / `[whispered]` markers — v3 features only
- ALL CAPS for whole sentences (sounds shouty, not emphasized)

---

## 6. Cadence-specific conventions

### Pause markers in source files

We use a markdown convention that the renderer translates to SSML:

| Source markup | Rendered output | Use case |
|---|---|---|
| `[PAUSE Xs]` | `<break time="X.0s"/>` (chained if X > 3) | Standard pauses |
| `[INHALE]` | `<break time="2.5s"/>` | Single inhale beat |
| `[EXHALE]` | `<break time="3.0s"/>` | Single exhale beat |
| `[BREATH IN — Xs]` | `<break time="X.0s"/>` (capped at 3) | Guided breath in |
| `[BREATH OUT — Xs]` | `<break time="X.0s"/>` (capped at 3) | Guided breath out |
| `[soft]`, `[firmer]`, `[warm]`, `[whispered]` | DROPPED (no effect) | Tone direction (documentation only) |
| `*italics*` | Markup stripped, plain text | (Use em-dashes or capitalization instead) |
| `(Stage direction in parens at line start)` | DROPPED | Not spoken |

### Session structure

Each session in a content file has frontmatter and a body separated by `---`:

```markdown
# Session 1 — "Why this works"

**Day:** 1
**Duration:** ~6 min
**Type:** Foundation lesson
**Goal:** Set the frame for the protocol.

---

[script body starts here]

Welcome to Cadence.

[PAUSE 2s]

[next paragraph...]
```

Frontmatter is NEVER spoken. Only content after the `---` divider becomes audio.

### Voice settings (in `voices.json`)

```json
{
  "voices": {
    "adam": {
      "voice_id": "s3TPKV1kjDlVtZbl4Ksh",
      "settings": {
        "stability": 0.55,
        "similarity_boost": 0.75,
        "style": 0.15,
        "use_speaker_boost": true
      }
    },
    "bella": { ... }
  }
}
```

Stability trade-off:
- **0.55** (current) — moderate variation, expressive, occasional drift on long sessions
- **0.70** — more consistent, slightly flatter, recommended if drift is observed
- **0.45** — more expressive, drift more likely

If a session's voice character drifts mid-session, raise stability for that voice and regenerate.

---

## 7. Workflow

### Editing existing scripts

1. Read this entire SKILL.md first if you haven't recently
2. Identify dense paragraphs (4+ substantive sentences) — add `[PAUSE 1s]` between thought groups
3. Identify short coupled phrases — leave alone (don't over-pause)
4. Verify the new break-tag density isn't excessive (see density caps table above)
5. Delete affected MP3 files in `audio_output/` and regenerate via `python onboarding.py` or `python -m audio.generate --all`
6. Listen end-to-end before claiming the edit is good

### Writing new scripts

1. Write first draft as natural prose — don't over-pause prematurely
2. Read it aloud (or have TTS read it) — listen for rushes
3. Add pauses where you actually heard a rush, not preemptively
4. Use the pause hierarchy in section 2 — punctuation first, breaks second
5. Audit dense paragraphs as above

### What to do if the audio sounds off

| Symptom | Likely cause | Fix |
|---|---|---|
| New sentence starts too quickly | Dense paragraph without internal breaks | Insert `[PAUSE 1s]` between thought groups |
| Word mispronounced | v2 unfamiliar with term | Pronunciation alias (see section 4) |
| Audio compressed / gibberish | Too many break tags | Reduce break density; consider silence-splicing pipeline for breath-paced content |
| Voice drifts character | Stability too low | Raise stability in voices.json from 0.55 to 0.70 |
| Lost emphasis on a word | Italics stripped | Replace with em-dash framing or ALL CAPS |
| Cut-off mid-word | Likely truncated stream | Delete the file, regenerate; `generate.py` now retries on under-size files |

---

## 8. Status (where this principle has been applied)

| Variant | Status |
|---|---|
| Variant A Week 1 | ✅ Applied — paragraph density edits + pause hierarchy |
| Variant A Weeks 2-8 | ⏳ Pending — apply same principle |
| Variant B all weeks | ⏳ Pending |
| Variant C all weeks | ⏳ Pending |
| Variant D all weeks | ⏳ Pending |
| Library scripts (breath, mindfulness, pre-session) | ⛔ Different problem — needs silence-splicing pipeline, not paragraph edits |

Estimated 30-45 min per week per variant to apply consistently once the pattern is internalized.

---

## 9. Where to read more

- **Live ElevenLabs docs:** https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices (or append `.md` for markdown)
- **AI agent index:** https://elevenlabs.io/docs/llms-full.txt (full docs in one file for context windows)
- **MCP server for Claude Code:** https://elevenlabs.io/docs/_mcp/server (if integrating live doc queries)
- **Cadence project docs:**
  - `audio/README.md` — pipeline overview
  - `content/_script_density.md` — earlier note on density (subsumed by section 3 here)
  - `qa_variant_a.md`, `qa_variants_bcd.md` — content QA findings
