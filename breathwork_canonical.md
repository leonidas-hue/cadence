# Cadence — Canonical Breathwork Spec & Rewritten Sessions

This defines the length, structure, and round count for every breathing exercise
in Cadence, grounded in the literature, plus drop-in rewritten scripts that fix
the "follow my counts" gap and the hold-timing bug. Use these as the source of
truth; adapt the *framing* per variant, keep the *structure* identical.

---

## 1. The length + round spec (evidence-based)

| Exercise | Pattern | Active-practice target | Guided rounds | Self-paced block | Notes / cap |
|---|---|---|---|---|---|
| **Box breathing** | 4-4-4-4 (in-hold-out-hold) | **2–3 min** (~8–11 rounds) | **3** (2 counted + 1 cued) | 60–120 s | Grounding/pre-event. Holds → lightheaded? shorten them. **Not for hypertonic (Variant B)** — see §4. |
| **4-7-8 (Relaxing Breath)** | 4-7-8 (in-hold-out) | **~75 s** | **4 total (2 counted + 2 cued)** | **none** | Beginner **hard cap = 4 cycles.** Build to 8 only after weeks. Ratio matters more than absolute seconds. |
| **Coherent / extended-exhale** | 5 in / 6 out (~5.5 bpm) | **5 min** (start 3–5, build 10–20) | **2** counted | 3–4 min | The daily calm baseline; longest breathwork. No holds → safe for everyone. |
| **Diaphragmatic (belly)** | 6 in / belly-led, ~6–8 bpm | **5 min** | **2–3** counted | 3–4 min | Foundational (Variant B). Even 5 min is useful. |

**Why these numbers, briefly:**
- Box: for acute stress 1–5 minutes is usually enough; for daily practice 5–10 minutes, and a common floor is at least four rounds, or as long as feels comfortable. Slowing to ~5 breaths/min engages respiratory sinus arrhythmia, but a 2025 study found six breaths per minute produced the strongest HRV increases, though box breathing still showed measurable effects — which is why box is our *grounding* tool and coherent breathing is our *baseline* tool.
- 4-7-8: Weil's own instruction is only four cycles in a row in the beginning; after you get used to it you can work up to eight, practiced twice daily. The exact count isn't sacred — it's a guideline; the 4:7:8 ratio is what matters. The cap is a safety feature, not an arbitrary limit, so 4-7-8 sessions guide all 4 cycles and do **not** invite extended self-practice.
- Coherent/extended-exhale: ~6 breaths per minute (5s in, 5s out) maximizes HRV and stimulates the vagus nerve; start with 3–5 minutes, some extend to 10–20 daily. It is the exhale, not the inhale, that most strongly activates the parasympathetic nervous system — hence our 5-in/6-out house pattern.
- Diaphragmatic: repeat for 5–10 cycles, work up to 10–20 minutes; even 5 minutes is genuinely useful, targeting 6–10 breaths per minute.

---

## 2. 2 vs 3 guided rounds — the decision

**It depends on technique complexity, and the guided portion should shrink over the 8 weeks.**

The principle from guided-practice pedagogy: use guided breathing as training wheels and silent breathing as the road test — e.g., guide to settle, then a silent stretch to practice self-directed returning, and gradually increase the silent portion over weeks.

- **Simple rhythms (coherent, extended-exhale, diaphragmatic): 2 counted rounds.** No holds to track; two reps lock the pace in, and over-guiding a simple rhythm feels patronizing.
- **Box breathing: 3 rounds (2 counted + 1 cued).** Two holds per round means more to track — people lose the rhythm fastest here, so the extra round earns its place as a bridge before silence.
- **4-7-8: guide all 4 (2 counted + 2 cued), no self-paced block.** The beginner cap is 4 cycles; you don't invite more.

**Program-level ramp (apply across the 8 weeks):**
- **Weeks 1–2:** full counting, shorter silent block (~60 s). Teaching phase.
- **Weeks 3–5:** drop to cue words, medium silent block (~90 s).
- **Weeks 6–8:** minimal cueing, longer silent block (~120–180 s). The user is self-pacing.

This also answers "are later sessions long enough": later sessions should get **more silence** (self-practice), not more talking. Extending a breathwork session means a longer silent block, never filler narration.

---

## 3. Pipeline requirement (must be in place before generating these)

These scripts assume two pipeline fixes are applied (see chat):
1. **Long pauses (`[PAUSE ≥10s]`) spliced as real silence** — already specced. Without it, every self-paced block collapses to 3 s.
2. **Holds (`[HOLD — Xs]`) spliced as real silence** in cued rounds — the small addition below. Without it, a 4 s hold renders as a 3 s break and the box isn't square; a 4-7-8 7 s hold is impossible as a single break tag.

Add to `splice.py` (mirrors the long-pause change):

```python
from .parser import HOLD_MARKER          # add to imports

# inside split_for_splicing(), in the per-line loop, alongside the breath checks:
        m = HOLD_MARKER.match(s)
        if m:
            flush()
            segments.append(SilenceSegment(float(m.group(1)), f"hold {m.group(1)}s"))
            continue

# and in needs_splicing():
    if HOLD_MARKER.search(body_md):
        return True
```

Cost: in *cued* rounds only, the cue word ("Hold.") becomes a ~1-word TTS clip
(a few per session). That's the price of an accurate hold; counted rounds avoid
it entirely by spelling the count out. Acceptable tradeoff for box/4-7-8 fidelity.

**Marker rule of thumb after the fixes:**
- `[PAUSE 1s]`–`[PAUSE 9s]` → single break tag (safe; used between counts).
- `[BREATH IN/OUT — Xs]`, `[HOLD — Xs]`, `[PAUSE ≥10s]` → real spliced silence.

---

## 4. Variant adaptation notes

- **Structure and timing are universal.** Only the framing changes per variant.
- **Variant B (hypertonic pelvic floor) must avoid breath holds.** Breath-holding
  recruits the pelvic floor and can reinforce the exact hypertonic pattern Variant B
  exists to fix. For Variant B, **drop box breathing and 4-7-8** in favor of
  **coherent (5-in/5-out, no holds)** and **extended-exhale / diaphragmatic**. If a
  grounding tool is needed under pressure, use a no-hold extended-exhale instead of box.
- **Variant A (anxiety-driven acquired):** box for grounding/pre-sex presence,
  extended-exhale for baseline. Frame around performance pressure.
- **Counting calibration:** counted rounds with `[PAUSE 1s]` between numbers land
  around 4–5 s per side (the spoken number eats ~0.4 s, the break ~1 s). That reads
  as a slightly slow, symmetric box — which is fine and arguably more calming. If you
  want tighter 4.0 s sides, trust the *self-paced* block for exactness and keep the
  counted rounds natural.

---

# 5. Rewritten sessions

Conventions: `[soft]`/`[firmer]` dropped at render. `[PAUSE Ns]` = break tag for
counting. `[BREATH IN/OUT — Xs]`, `[HOLD — Xs]`, long `[PAUSE]` = spliced silence.

---

## 5A. Box breathing — replaces Variant A, Session 5

> 2 counted rounds → 1 cued round → ~90 s self-paced. Active ≈ 3 min; total ≈ 6 min.

Today we add a second breath tool to your kit.

[PAUSE 2s]

Extended exhale — what we've been practicing — is for a calm baseline. We use it before bed, before sex, whenever we want to feel slower.

[PAUSE 2s]

Box breathing is different. It's for *under pressure*. Special operations soldiers use it, surgeons use it, athletes use it between points. It resets you fast when you're in the middle of something stressful.

[PAUSE 2s]

The shape is a square: four seconds in, four-second hold, four seconds out, four-second hold. I'll count the first rounds with you, then you'll take it on your own.

[PAUSE 2s]

Get comfortable. Hand on your belly. Let's settle with three slow breaths first.

[soft]
In.
[BREATH IN — 4s]
And out, slow.
[BREATH OUT — 6s]

[soft]
In.
[BREATH IN — 4s]
Out.
[BREATH OUT — 6s]

[soft]
In.
[BREATH IN — 4s]
Out.
[BREATH OUT — 6s]

[PAUSE 2s]

Now the box. Follow my count.

[firmer]
Breathe in.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Hold.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
And out.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Hold.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.

[PAUSE 1s]

[firmer]
Again. Breathe in.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Hold.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Out.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Hold.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.

[PAUSE 2s]

[soft]
Good. One more, and this time I'll just name each side. You keep the count in your head.

[firmer]
In.
[BREATH IN — 4s]
Hold.
[HOLD — 4s]
Out.
[BREATH OUT — 4s]
Hold.
[HOLD — 4s]

[PAUSE 2s]

Now continue on your own. Four counts each side of the box. If you lose track, just start a new square. I'll bring you back in about ninety seconds.

[PAUSE 2s]

Begin.

[PAUSE 90s]

[soft]
Come back. Let your breath go normal.

[PAUSE 3s]

If you ever feel lightheaded with the holds, that's your cue to shorten them — three counts, or even two. The square just needs to be even, not long.

[PAUSE 2s]

Box breathing has a different feel than extended exhale. Less softening, more grounding. It puts you in your body without making you sleepy. This is the breath for thirty seconds before sex starts — not to get drowsy, to get *present*.

[PAUSE 2s]

Practice it in dead moments during the day. Waiting for an elevator. Stuck in traffic. Make it boring and familiar, so under real pressure your body already knows it.

[PAUSE 2s]

Good work.

---

## 5B. 4-7-8 (Relaxing Breath) — canonical practice block

> 2 counted + 2 cued = all 4 cycles. No self-paced block (respect the cap). Active ≈ 75 s; total ≈ 4–5 min with intro/outro.

This one is a natural tranquilizer. Inhale quietly through the nose for four, hold for seven, then exhale through the mouth for eight with a soft whoosh. The long exhale is the part that flips your system into calm.

[PAUSE 2s]

One detail: rest the tip of your tongue just behind your top front teeth, and keep it there. You'll exhale around it.

[PAUSE 2s]

We do exactly four breaths — no more, especially while you're learning. If the seven-count hold feels long, speed the whole thing up but keep the rhythm four, seven, eight. Let's go. First, empty your lungs completely.

[BREATH OUT — 4s]

[firmer]
Breathe in through your nose.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Hold.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Five.
[PAUSE 1s]
Six.
[PAUSE 1s]
Seven.
[PAUSE 1s]
And out, whoosh.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Five.
[PAUSE 1s]
Six.
[PAUSE 1s]
Seven.
[PAUSE 1s]
Eight.

[PAUSE 2s]

[firmer]
That's one. Again — in through the nose.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Hold.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Five.
[PAUSE 1s]
Six.
[PAUSE 1s]
Seven.
[PAUSE 1s]
Out, whoosh.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Five.
[PAUSE 1s]
Six.
[PAUSE 1s]
Seven.
[PAUSE 1s]
Eight.

[PAUSE 2s]

[soft]
Two more, and now I'll just name the phases. Keep the count yourself.

[firmer]
Inhale.
[BREATH IN — 4s]
Hold.
[HOLD — 7s]
Exhale, whoosh.
[BREATH OUT — 8s]

[firmer]
Last one. Inhale.
[BREATH IN — 4s]
Hold.
[HOLD — 7s]
Exhale, all the way out.
[BREATH OUT — 8s]

[PAUSE 3s]

[soft]
Let your breathing return to normal. Notice how your body feels now versus a minute ago.

[PAUSE 3s]

That's the whole practice — four breaths, twice a day. It gets more powerful the more you use it, not less. Use it before anything that spikes your nerves.

[PAUSE 2s]

Good work.

---

## 5C. Coherent / extended-exhale — canonical baseline block (no holds)

> 2 counted rounds → ~4 min self-paced. Active ≈ 5 min. Safe for all variants, including Variant B.

This is your baseline breath — the one you'll use most. Five seconds in, six seconds out. The slightly longer exhale is doing the work; that's what tells your nervous system it's safe to slow down.

[PAUSE 2s]

Hand on your belly. The belly should rise on the inhale, fall on the exhale. Chest stays quiet. Let's set the pace together.

[firmer]
Breathe in.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Five.
[PAUSE 1s]
And out.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Five.
[PAUSE 1s]
Six.

[firmer]
Again. In.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Five.
[PAUSE 1s]
Out, longer.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Five.
[PAUSE 1s]
Six.

[PAUSE 2s]

[soft]
You have the rhythm. Keep it going on your own now — in for five, out for six. Belly soft. I'll stay quiet for a few minutes; let the breath get boring and easy.

[PAUSE 2s]

Begin.

[PAUSE 120s]

[soft]
Keep going if it feels good.

[PAUSE 120s]

[soft]
And let it return to normal.

[PAUSE 3s]

This is the breath for before sleep, before sex, and any time your arousal or your nerves start climbing faster than you want. The longer the exhale, the stronger the brake.

[PAUSE 2s]

Good work.

---

## 5D. Diaphragmatic (belly) breathing — canonical foundational block

> 2–3 counted breaths → setup → ~4 min self-paced. Active ≈ 5 min. Variant B foundation.

Today is about *where* the breath goes, not how fast. We want the breath low — into the belly, not high in the chest.

[PAUSE 2s]

Lie on your back, knees bent, or sit upright. One hand on your chest, one on your belly. As you breathe, the belly hand should move; the chest hand should stay almost still.

[PAUSE 3s]

Let's find it together. Breathe in slowly and send the air down, so the belly rises under your hand.

[firmer]
In, belly rises.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Five.
[PAUSE 1s]
Six.
[PAUSE 1s]
And let it fall.
[PAUSE 1s]
Two.
[PAUSE 1s]
Three.
[PAUSE 1s]
Four.
[PAUSE 1s]
Five.
[PAUSE 1s]
Six.

[firmer]
Again. In, low and slow.
[BREATH IN — 5s]
Soften, and out.
[BREATH OUT — 6s]

[soft]
One more, and feel only the belly hand move.
[BREATH IN — 5s]
Out.
[BREATH OUT — 6s]

[PAUSE 2s]

[soft]
Now keep that going on your own. Don't force a big breath — just let it be full and low. If your mind wanders, come back to the belly hand. I'll be quiet for a few minutes.

[PAUSE 2s]

Begin.

[PAUSE 120s]

[soft]
Still with the belly. Easy and full.

[PAUSE 120s]

[soft]
Let it return to normal, and notice how your body feels.

[PAUSE 3s]

This low, slow breath is the foundation everything else builds on. The more it becomes your default, the more your whole system stays in the calm gear — which is exactly where control lives.

[PAUSE 2s]

Good work.
