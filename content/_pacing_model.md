# Pacing & Intensity Model

How users move through the program. Two **independent** settings, plus the always-available practice library.

This model replaces an earlier version that bundled "advancement speed" and "daily time commitment" into a single 3-option slider (standard / intensive / extended). The earlier model included an "intensive mode" that compressed the 8-week program into 4 weeks at 2 sessions/day. That option has been deliberately removed; see "What we removed and why" below.

---

## Two independent settings

### Setting 1: Advancement speed (how fast through the 8 weeks)

| Value | Cadence | When to use |
|---|---|---|
| `standard` (default) | One core session per day, 8 weeks total | Default for nearly all users |
| `extended` | One core session every 2 days, ~16 weeks total | When life is busy or daily cadence overwhelms |

Notes:
- Day 1 → Day 2 unlocks immediately on first launch (Day 1 is informative; forcing 24h wait feels artificial). Normal pacing resumes from Day 2.
- Auto-suggest switching to `extended` if a user misses 3+ consecutive days. Don't auto-switch; just suggest.

### Setting 2: Daily time commitment (how much time per day)

| Value | Daily time | Composition |
|---|---|---|
| `quick` | 5-10 min | Core session only |
| `standard` (default) | 15-25 min | Core + one daily add-on |
| `extended` | 30-45 min | Core + add-ons + practice library stack |
| `deep` | 45-60 min | Core + add-ons + library stack + reflection/journaling |

Notes:
- Independent of advancement speed. A user on `extended` advancement (every 2 days) can still pick `deep` daily time on practice days.
- Hard caps enforced per practice type regardless of tier (see next section).

---

## Hard caps per practice type

These caps exist because of dose-response evidence. They override the user's daily time tier if the tier would push past a cap. See the design rationale doc for sources.

| Practice | Daily cap | Why |
|---|---|---|
| Pelvic floor exercises | 15 min/day | Past this, risk of hypertonic patterns (which is what Variant B exists to fix) |
| Stop-start / paced edging | 2-3 sessions per week (not per day) | Clinical guidance: nervous system needs consolidation between practice sessions |
| Mindfulness / meditation | 45 min/day soft cap | Past this, diminishing returns documented in meta-analyses |
| Breath practice | 30 min/day soft cap | Same — diminishing returns past this |
| Body awareness / scan | 20 min/day soft cap | Plateaus |
| Sensate focus (partnered) | Time-bound by the activity | Not a daily-volume metric |
| Educational lessons | One play, optional re-listen | Re-listening helps integration, not duration |

These caps mean: a `deep`-tier user is offered ~55 min of legitimate practice composed from compounding low-harm practices, not 60 min of pelvic floor work.

---

## The practice library (always available)

These sessions live outside the daily core program. Users can launch any of them, any time, any number of times per day (subject to the caps above). No unlock gates.

| Session | Source | Notes |
|---|---|---|
| Breath — Calm (4-6) | `shared_breathwork_practice.md` | Endlessly repeatable |
| Breath — Ground (box) | `shared_breathwork_practice.md` | Pre-event use case |
| Breath — Settle (4-7-8) | `shared_breathwork_practice.md` | Evening / sleep use case |
| Body scan | derived from `variant_a_week_1` day 3 | Reusable awareness skill |
| Mindfulness — Daily | `addon_mindfulness_daily.md` | 7 min |
| Pre-session prep — long | `shared_pre_session_prep.md` | ~10 min, before partnered sex |
| Pre-session prep — short | `shared_pre_session_prep.md` | ~6 min |
| PFM — light maintenance | derived from `variant_a_week_1` day 6 | Variant A users; daily-allowed |
| PFM — reverse Kegels | from variant_b content | Variant B core skill; daily for B users |
| Edging — paced solo | `shared_edging_solo.md` | Variants C, D, and A wk 2+; **gated by weekly cap** |
| Daily reflection / journaling | `shared_journaling_prompts.md` | Text prompts, week-themed |

---

## Daily plan assembly logic

The app's "Today" screen is built dynamically:

```
INPUTS
- variant: A | B | C | D
- advancement_speed: standard | extended
- daily_time_commitment: quick | standard | extended | deep
- addons opted in: pelvic | breathwork | mindfulness
- current_program_day: int
- last_session_completed: timestamp
- this_week_edging_count: int  (for the stop-start cap)

OUTPUT
{
  primary: <core session for the current program day>,
  also_today: [
    <add-on sessions from explicit opt-ins>,
    <library suggestions composed to hit time tier without breaching caps>
  ],
  unlocked_library: [<all practice library sessions, with cap warnings if applicable>]
}
```

### Composition rules

1. **Primary is always the core session.** Never skipped or replaced.
2. **Explicit add-ons** (mindfulness/breath/PFM) come next.
3. **Library stack** fills remaining time toward the tier target, biased toward:
   - Breath, mindfulness, body scan (high benefit per minute, no caps usually triggered)
   - Reflection/journaling for `deep` tier
   - Pre-session prep when user indicates partnered sex tonight
4. **Caps override tier target.** If the user is at `deep` (45-60 min) but has already done 2 edging sessions this week, the composer doesn't suggest a 3rd — it suggests reflection or library instead.

### Concrete examples

**Variant A user, day 3, standard advancement, standard time, mindfulness add-on:**
- Primary: "Body scan and the clench" (8 min)
- Also today: Mindfulness daily (7 min)
- Total: ~15 min ✓

**Variant A user, day 3, standard advancement, deep time, mindfulness add-on:**
- Primary: "Body scan and the clench" (8 min)
- Add-on: Mindfulness daily (7 min)
- Library stack: Body scan from library (10 min), breath Calm pattern (5 min), light PFM maintenance (5 min), reflection prompts (10 min), pre-session prep if relevant (10 min)
- Total: ~55 min ✓
- Caps: PFM at 5 min (well under 15); no edging suggested (week 1 doesn't include it for A anyway)

**Variant B user, day 22, standard advancement, deep time:**
- Primary: "Reverse Kegels — extended practice" (~9 min)
- Library stack: Diaphragmatic breath (5 min), body scan (10 min), mindfulness (7 min), reflection prompts (10 min)
- PFM cap: total PFM-related time stays under 15 min (the core session is the PFM work; library suggestions don't add to it)
- Total: ~50 min ✓

**Variant D user, day 20, standard advancement, deep time:**
- Primary: "Adding the cycle" (~6 min + 20 min self-directed practice)
- Library stack: Mindfulness (7 min), reflection (10 min), breath calm (5 min)
- Edging cap: this is the 3rd edging-adjacent session this week, so no library-edging suggested
- Total: ~50 min ✓

---

## What we removed and why

### Removed: "Intensive mode" (2 core sessions/day — finish in 4 weeks)

The earlier model offered this as the "high-engagement" option. We removed it because:

1. **The protocols have internal pacing logic.** Day 15's stop-start work assumes Day 14's content has consolidated, which requires a calendar day of non-practice. Compressing produces faster *advancement* but worse *outcomes* — the user finishes "week 8" without the actual skills having locked in.

2. **It conflated "more engagement" with "faster completion."** Users who think they want intensive mode are usually pattern-matching to gym-culture "more reps = more gains." That doesn't apply here. For PE-specific practices, more isn't better past surprisingly low daily volumes.

3. **It's a footgun.** Power users will gravitate to it, then complete the program without skills having properly consolidated, then report the program didn't work.

The right design for users who want more engagement is **more parallel practice in a single day** (mindfulness, breath, body work, reflection), not **faster program advancement**. The new `daily_time_commitment = deep` tier serves exactly this need.

---

## Adherence tracking

Track adherence by **core sessions completed**, not by calendar days. This way:
- A user on `extended` advancement (every 2 days) isn't penalized for "missing" days
- A user who occasionally skips a day picks up the next session, not the next calendar day

Practice library completions are tracked separately and shown on the progress chart but don't count toward program advancement.

---

## Implementation notes

- `advancement_speed` and `daily_time_commitment` live in `questions.json` (preferences section, asked post-routing)
- The plan-composer function lives at the app layer (Flutter), not in `routing.py`. Routing decides the variant; the composer assembles the daily plan.
- Caps are constants in the composer. They should not be user-adjustable; making them so reintroduces the footgun.
- The `shared_journaling_prompts.md` module is **not yet written**. It's needed for the `deep` tier to make sense. Spec: text-only (no audio), week-themed prompts, one per day, the user responds in the app and can review responses over time. Cheap content, high value for high-time users.
