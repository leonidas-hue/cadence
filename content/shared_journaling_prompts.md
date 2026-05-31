# Shared — Journaling / Reflection Prompts

**Status:** SPEC ONLY — content not yet written.
**Type:** Text-based daily reflection prompts (no audio).
**Used by:** `daily_time_commitment = deep` tier across all variants.
**Daily time:** ~10 min for the user to read prompt + respond in writing.
**Voice direction:** N/A — this is text. But the prompt phrasing should match the variant's voice character (matter-of-fact, non-moralizing, treats the reader as capable).

---

## Why this module exists

The `daily_time_commitment = deep` tier (45-60 min/day) needs a way to legitimately fill time beyond the core session and the standard add-ons. The available audio practices have caps:

- PFM work caps at 15 min/day (hypertonic risk)
- Stop-start caps at 2-3 sessions/week (consolidation requirement)
- Mindfulness, breath, body scan have soft caps around 20-45 min

So a deep-tier user with all add-ons enabled is at roughly 35-40 minutes of legitimate audio practice. Reflection/journaling closes the gap to 60 min without harm.

Beyond filling time, this module produces real value:
- **Generates self-data** the user can review later (week 4 reflection can reference week 1 entries)
- **Compounds with the protocol's awareness work** — Variant A's spectatoring, Variant B's connected-tension scanning, Variant D's pattern-noticing all benefit from written reflection
- **Cheap to build** — text prompts, no audio generation, no voice talent, no studio
- **Cheap to maintain** — once written, prompts don't require regeneration when voices change

---

## Structure

### One prompt per day, 56 days × 4 variants = 224 prompts total
### Prompts are variant-aware

Each variant has its own prompt sequence, themed to its weekly arcs:

**Variant A (anxiety-driven):**
- Week 1: noticing the body during ordinary moments
- Week 2: when does sympathetic activation show up in daily life
- Week 3: communication patterns with partner (if applicable)
- Week 4: where does the catastrophic narrative run beyond sex
- Weeks 5-8: integration prompts, reviewing earlier responses

**Variant B (hypertonic):**
- Week 1: locating the clench in daily life
- Week 2: the four connected tension zones in your day
- Week 3: which cognitive patterns (vigilance, hypercontrol) showed up today
- Week 4: what does "released floor during arousal" feel like internally
- Weeks 5-8: integration + the broader release-as-life-skill thread

**Variant C (lifelong/hypotonic):**
- Week 1: relationship to your own timing — historical and current
- Week 2: what does patience feel like in this work
- Week 3: stop-start session debriefs (what surprised you)
- Week 4: reverse Kegel notes
- Week 5: pharma reflection (if pursuing) or non-pursuit reasoning
- Weeks 6-8: integration

**Variant D (porn-conditioned):**
- Week 1: observation notes (no change yet)
- Week 2: grip session debriefs
- Week 3: pace + visual stimulus debriefs
- Week 4: branched — current users reflect on taper; past users on transfer work
- Week 5: branched continuation
- Weeks 6-8: integration, post-experiment for current users

---

## Prompt shape

Each daily prompt has three parts:

1. **A specific question** (not "how did you feel today?" — something like "Where in your body did you notice tension during your work day? Be specific about location and intensity.")
2. **An optional observation prompt** — something to notice but not write about, that primes the question
3. **A short closing** — one sentence acknowledging the work

Example for Variant A Week 1 Day 3 (after "Body scan and the clench"):

> Today's reflection.
>
> The body scan today asked you to notice unconscious tension. Now, ten or fifteen minutes after the session, take stock again:
>
> **Where is your body holding tension right now? Be specific: which muscle, what intensity (1-10), and what were you doing when you first noticed it?**
>
> No need to release the tension before answering. Just locate it.
>
> Two or three sentences is fine. You're collecting data about your own body, not writing an essay.

---

## What the app shows

A simple text field below the day's audio session. The prompt is the placeholder/header. The user types their response. Saved locally. Browsable by date or by theme (e.g., "show me all my Week 1 entries about tension").

In the v1 app: SQLite via Drift, one row per response, just `(date, variant, week, day, prompt_id, response_text)`. Nothing fancy.

---

## What this module does NOT do

- Does not generate audio
- Does not gate anything (skipping reflection doesn't block advancement)
- Does not analyze the user's responses (no NLP, no sentiment scoring, no "you seem stressed")
- Does not surface responses back as motivational quotes
- Does not export by default (privacy)

---

## When to actually write this content

After the audio refinement work is done and the four variants are voice-validated. The prompts will draw on session-specific content for context, so they should be written *after* any session-level edits have settled. Premature writing means rework.

Realistic estimate: 4-6 hours of focused writing once the prerequisites are clear. ~224 prompts × ~3-5 sentences each, mostly variation on a small set of templates that adapt to the day's content.
