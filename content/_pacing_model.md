# Pacing & Intensity Model

How users move through the program. The structure is the same content library, three pacing modes, plus an always-available practice library.

---

## The three pacing modes

### 1. Standard (default)
- One core session per day
- Days unlock in sequence; one per calendar day
- Exception: Day 1 of week 1 → Day 2 unlocks immediately (Day 1 is purely informative; forcing a 24h wait feels artificial)
- After Day 2, normal one-per-day pacing resumes

### 2. Intensive (opt-in)
- Up to 2 core sessions per day
- Triggered by: user finishes a session and immediately taps "next session" twice in week 1, OR user toggles "Intensive mode" in settings
- We surface a one-time prompt the first time the pattern appears: *"Want to keep going? You can do an extra session today."*
- The full 8-week program completes in 4 weeks at this rate
- We don't push intensive — we let the user discover it

### 3. Extended (opt-in)
- One core session every 2 days
- For users who feel overwhelmed or have low time
- Triggered by user toggle in settings, or auto-suggested if user misses 3+ consecutive days
- The 8-week program runs ~16 weeks at this rate

---

## The practice library (always available)

These sessions live outside the daily core program and the user can launch any of them, any time, any number of times per day. No unlock gates.

| Session | From | Why it's library-only |
|---|---|---|
| Breath — Calm (4-6) | shared_breathwork_practice | Endlessly repeatable; no progression needed |
| Breath — Ground (box) | shared_breathwork_practice | Pre-event use case |
| Breath — Settle (4-7-8) | shared_breathwork_practice | Evening / sleep use case |
| Body scan | derived from variant_a_week_1, day 3 | Reusable awareness skill |
| Mindfulness — Daily | addon_mindfulness_daily | Daily add-on |
| Pre-session prep — long | shared_pre_session_prep | On-demand before partnered sex |
| Pre-session prep — short | shared_pre_session_prep | On-demand, time-constrained |
| PFM — light maintenance | derived from variant_a_week_1, day 6 | Variant A users; daily-allowed |
| PFM — reverse Kegels practice | from variant_b content (forthcoming) | Variant B core skill |
| Edging — paced solo | forthcoming | Variants C, D + A wk 2+ |

This means: **a high-intent user could do their core session, then a breath practice, then mindfulness, then body scan — all in one day** without needing any new content from us.

---

## Daily plan assembly logic

The app's "Today" screen is built dynamically from these inputs:

```
INPUTS
- variant: A | B | C | D
- pacing_mode: standard | intensive | extended
- preferences:
    - addon_pelvic: yes | no
    - addon_breathwork: yes | no
    - addon_mindfulness: yes | no
- session_time: 5 | 10 | 15 | 20+
- last_session_completed: timestamp
- current_program_day: int

OUTPUT
{
  primary: <core session for the user's current program day>,
  also_today: [
    <add-on sessions opted into>,
    <"continue if you have time" suggestions based on session_time>
  ],
  unlocked_library: [<all practice library sessions>]
}
```

### Concrete example: Variant A user, day 3, standard pacing, mindfulness add-on, 15-min commitment

- **Primary:** "Body scan and the clench" (8 min)
- **Also today:** Mindfulness daily (7 min)
- **Library:** All breath patterns, pre-session prep, body scan, PFM light, mindfulness — accessible any time

Total time: 15 min if they do everything. Their session_time of 15 was honored.

### Concrete example: Variant A user, day 3, intensive pacing, all add-ons, 20+ min commitment

- **Primary:** "Body scan and the clench" (8 min)
- **Optional second core:** Day 4 lesson "Spectatoring" available (6 min)
- **Also today:** Mindfulness daily (7 min), supplementary PFM (5 min)
- **Library:** Same as before

Total time: 26 min if they do everything. They've consumed 2 days of program in 1 calendar day.

---

## What this DOES NOT do

- Does not produce more unique audio content
- Does not change the variant assignment
- Does not let users skip sessions they're not ready for (sequential lock for *core* sessions still applies, just compressed)
- Does not bypass safety-critical gates (Variant B users still cannot access standard Kegel content — that's protocol-level, not pacing-level)

---

## Implementation notes

- The "intensive mode discovery prompt" is an A/B test candidate for v2. For v1 we just expose the toggle in settings.
- Track adherence by *core sessions completed*, not by calendar days. A user on intensive who completes 14 core sessions in 7 days is at "Day 14" of the program.
- Practice library completions are tracked separately and shown on the progress chart but don't count toward program advancement.
