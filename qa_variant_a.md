# Variant A — QA Findings

Five-pass review of all 8 weeks of Variant A content (~58 unique scripts).

**Passes run:**
1. Tonal consistency across 8 weeks
2. Factual accuracy / claims audit
4. Dependency and continuity check
5. Tonal failure-mode check
7. Inclusivity and assumption check

Severity scale used:
- 🔴 **Fix before beta** — incorrect, harmful, or alienating
- 🟡 **Fix before launch** — credibility risk, will draw criticism
- 🔵 **Worth considering** — improvement, not blocker
- ⚪ **Note** — observation, no action needed

---

## Action items at a glance

| # | Severity | Pass | Location | Issue |
|---|---|---|---|---|
| 1 | 🔴 | 2 | Day 23 | "duration plateaus quickly" overstates evidence — Brody/Costa research shows the opposite for orgasm consistency |
| 2 | 🟡 | 2 | Day 15 | "gold standard for performance-anxiety-driven sexual issues" / "fastest results in clinical settings" — overclaim |
| 3 | 🟡 | 2 | Day 1 | "Many users see meaningful improvement in 4-6 weeks" — no clinical timeline data backs this |
| 4 | 🟡 | 2 | Day 27 | "duration is rarely the top answer" partially correct but understated; control over ejaculation IS centrally important to partners |
| 5 | 🟡 | 5 | Day 24 | "I've realized I've been treating your pleasure like it's my homework" — script puts a specific, clever line in the user's mouth |
| 6 | 🟡 | 7 | Days 18p, 19p, 20p, 27, 53 | Heterosexual + male-with-female-partner default throughout; gay/bi men using Variant A get an awkward fit |
| 7 | 🟡 | 4 | Day 7 → Days 36–42 | Recovery sequence on Day 37 references behaviors not yet introduced |
| 8 | 🔵 | 1 | Weeks 5–8 | The reflective register from week 7 onward feels like a different voice than weeks 1–4. Not a problem, but worth flagging for ElevenLabs prompt engineering |
| 9 | 🔵 | 5 | Day 47 | "If you have a substance use question…" — could land as judgmental for the user who uses cannabis recreationally without issue |
| 10 | 🔵 | 4 | Day 11 | Sensate focus solo "no genital touching" instruction conflicts with the Day 18s longer solo session which says "including the genitals this time" — needs explicit reconciliation |
| 11 | 🔵 | 2 | Day 9 | "Half of all men finish faster than that. Half finish slower." — true by definition of median, but slightly misleading framing in context |
| 12 | 🔵 | 7 | Day 1 onwards | "Your partner" assumed singular; doesn't fit polyamorous or casual-multiple-partner users |
| 13 | ⚪ | 1 | All weeks | "Good work today" appears at end of ~30 sessions. Acceptable, but worth knowing for voice variety |
| 14 | ⚪ | 5 | Day 45 | "The man you're becoming" session has identity-aspirational tone that some users may find uncomfortable |
| 15 | ⚪ | 4 | Days 18p–20p partnered path | All assume the partner agrees on Day 18p. No content for "partner said no, now what" beyond a sentence in 18p |

---

## PASS 1 — Tonal consistency across the 8 weeks

### Strengths

The voice holds together remarkably well across 56 sessions. Specific things that work:

- **The opening pattern is consistent.** Weeks 1, 2, 3, 4, 5, 6, 7, 8 all begin with "Welcome to week X" — small thing, but creates a real ritual.
- **Direct address ("you") used throughout, never lapses into clinical third person.** This was a tonal risk and it didn't materialize.
- **Brevity discipline holds.** No session bloats past its stated time, and the closings stay short (Day 7 closing through Day 56 closing all sit between 4–6 minutes).
- **The "[firmer]" / "[soft]" markers are used consistently for similar functional purposes** — [firmer] for instruction, [soft] for transitions and openings.

### Issues found

**🔵 #8 — Reflective register shift in weeks 7–8**

Weeks 1–4 have a voice that is direct, instructional, sometimes warm but always purposeful. Weeks 7–8 — particularly Day 45 ("The man you're becoming") and Day 55 ("What you've actually built") — shift into a noticeably more reflective, almost ceremonial voice. Listen to these passages back-to-back:

> Week 1, Day 1: *"This protocol takes more daily work than the others. Five to ten minutes of pelvic floor work most days."* — direct, instructional

> Week 7, Day 45: *"A man who breathes deeply by default. Not consciously — automatically. Whose nervous system runs in parasympathetic state most of the time, not sympathetic. Whose baseline is calm, not braced."* — almost incantatory

This isn't necessarily wrong — the program is intentionally shifting from technique to identity in week 7. But the voice may feel like a different person to listeners. Two options:

- **Option A:** Accept the shift as intentional. Generate the audio and listen — it may sound natural in the voice actor's delivery.
- **Option B:** Rewrite Day 45 in the more direct register of weeks 1–4, while keeping the content the same. Maybe trade some of the lyricism for declarative sentences.

I lean Option A — the shift mirrors the actual structure of the program, and the content earns the slightly different voice. But worth a second listen post-generation.

**⚪ #13 — Session-closing repetition**

Counted: "Good work today" or "Good work" appears at the end of approximately 30 of 56 sessions. Other variants: "See you in week X" (8 sessions, week-closing days), "Take care of yourself" (Day 56 only), no closing (rare). This is fine — closing rituals should be consistent — but if voice generation reveals the line landing flat, it's an easy place to vary.

Suggested alternates if needed: "Well done." / "That's it for today." / "See you tomorrow." Use sparingly so the main closing stays the recognizable signature.

**⚪ — "Spectatoring" usage**

The word appears in Day 4, Day 13, Day 24, Day 26, Day 45 — five times across the program. Healthy frequency for a key concept; not overused.

### No issues found

- No voice drift between Adam-coded and Bella-coded content (single voice throughout, generated separately later).
- No tonal inconsistency between weeks within the same voice.
- No instances of the voice "remembering" something it shouldn't, or "forgetting" something it set up.

---

## PASS 2 — Factual accuracy / claims audit

I researched the most consequential empirical claims. Here's what holds up, what needs softening, and what needs correcting.

### Claims that hold up well

**✅ IELT median 5–7 minutes (Day 23).**
Waldinger's 2005 multinational survey (5 countries, n=500 couples, stopwatch-timed) found a median IELT of 5.4 minutes. The 2009 follow-up using a blinded timer device found a median of 6.0 minutes. "Between five and seven minutes" sits squarely within the supported range. *Keep as-is.*

**✅ Clinical PE threshold around 1–2 minutes (Day 23).**
Waldinger proposed the 0.5 percentile (IELT < 1 min) as "definite" PE and 0.5–2.5 percentile (1–1.5 min) as "probable" PE. DSM-5 uses ~1 minute as the cutoff for lifelong PE. My phrasing "under one to two minutes consistently" is accurate. *Keep.*

**✅ Sex therapist "adequate" range 3–7 minutes (Day 23).**
Corty & Guardiani 2008 surveyed 34 SSTAR sex therapists. Their result: "adequate" = 3–7 min, "desirable" = 7–13 min, "too short" = 1–2 min. The framing in Day 23 — "Going from one minute to four minutes is clinically significant. So is going from two minutes to six" — maps directly onto this. *Keep.*

**✅ Partner distress framing on Day 27.**
The Burri et al. 2014 study (1,463 women in Mexico, Italy, South Korea) found that the most common reason for female partner distress was "lack of attention he pays to her other sexual needs due to him being caught up by his condition" — *not* the short duration itself. This is exactly the framing I used. *Keep, with one minor softening — see issue #4.*

### Claims that need correction or softening

**🔴 #1 — Day 23: "duration plateaus quickly" overstates the evidence**

My text:
> *"But once you're above three to four minutes, additional duration mostly stops mattering. Studies asking what predicts satisfaction find that the duration variable plateaus quickly."*

Problem: Brody & Weiss 2010 found women's orgasm consistency *positively correlates* with PVI duration, and the effect persisted controlling for age and was not driven by sub-1-minute outliers. The "duration plateaus" claim is more of a clinical practitioner heuristic than an empirically robust finding. Some studies show plateau-ish effects, others (like Brody/Weiss) show monotonic positive correlation.

**Recommended rewrite:**
> *"But once you're above three to four minutes, the relationship between additional duration and satisfaction gets weaker. Other factors — emotional connection, presence, communication, novelty, foreplay quality — start doing more of the predictive work. Some research does show longer intercourse correlating with women's orgasm consistency, so duration isn't irrelevant — it's just one of several variables, and not the dominant one once you're out of the clinical-PE range."*

This is more honest and less debunkable. Should be applied directly.

**🟡 #2 — Day 15: "gold standard" / "fastest results in clinical settings"**

My text:
> *"The behavioral evidence on PE strongly favors partnered work. Sensate focus done with a partner, applied stop-start with a partner — these are the techniques the original studies validated, and they're what produce the fastest results in clinical settings."*

Problem: Cooper et al. 2015 systematic review of 10 RCTs concluded "there is *limited* evidence that physical behavioral techniques for PE improve IELT and other outcomes over waitlist." Two of the four waitlist-controlled trials they reviewed showed *no benefit* for behavioral therapy alone. The strongest evidence is for **combination therapy** (behavioral + drug), not behavioral alone.

The "gold standard" framing is the clinical-practice consensus, but isn't well-supported by the systematic-review-level evidence. Sensate focus & stop-start are widely used clinically, but "produce the fastest results" is a stretch.

**Recommended rewrite:**
> *"The behavioral techniques with the most clinical history for performance-anxiety-driven PE are sensate focus and applied stop-start with a partner. These are what Masters & Johnson originally validated, and what most sex therapists still use in their practices today. The published evidence is mixed — some randomized trials show meaningful gains, others show smaller effects — but in clinical practice, partnered work tends to produce results faster than solo work alone."*

This concedes the actual evidence picture without undercutting the protocol.

**🟡 #3 — Day 1: "fastest-responding profile"**

My text:
> *"This is the fastest-responding profile. Many users see meaningful improvement in 4-6 weeks."*

Problem: There's no published clinical timeline data that says anxiety-driven acquired PE responds faster than other profiles to a CBT-style protocol over 4–6 weeks. The intuition is reasonable — acquired profiles have been shown to respond better than lifelong in some studies — but the specific 4–6 week claim is invented for the script.

**Recommended rewrite:**
> *"This is generally a more responsive profile than lifelong PE — there's a clear cause (anxiety) that the protocol directly targets. Most users start to notice changes by week 4–6, though everyone's timeline is different."*

The shift: stop saying "fastest-responding" as if it's a research finding, and shift "many users see meaningful improvement" → "most users start to notice changes" (softer, harder to disprove).

**🟡 #4 — Day 27: minor softening of "duration is rarely the top answer"**

My text:
> *"When women whose partners have PE are asked what would matter most to them about the situation, duration — the actual minutes — is rarely the top answer. The top answers are emotional engagement, presence, communication, and reduced anxiety in their partner."*

Problem: The Patrick et al. and Hobbs et al. qualitative studies found that "lack of control over ejaculation" is centrally important to partners and is a primary source of distress. Duration is not unimportant to partners; it's just that the way it shows up in distress isn't usually as a clock concern but as a "you're caught up in your condition" concern.

**Recommended rewrite:**
> *"When women whose partners have PE are asked what bothers them most, duration — the actual minutes — is rarely the top answer. The top answers cluster around something else: a sense that their partner is too caught up in his own performance to be present with them, that there's a missing emotional engagement, that their other sexual needs go unnoticed because of how anxious he is about timing. Control over ejaculation matters, but it tends to matter less as a clock concern and more because lack of control is what's making him absent."*

This preserves the message (which is supported) without overstating the absence of duration concerns.

**🔵 #11 — Day 9: "Half of all men finish faster, half finish slower"**

True by definition of median. But in the context of the Day 9 explanation, where I'm establishing the arousal scale, this brief statistical aside might be confusing — it sounds like I'm saying half of all men have PE. Better framing: just give the number ("the median is around 5–6 minutes") without the median-explanation aside, since it's not load-bearing for the lesson.

### Methodological note on what I didn't audit

- **Pelvic floor / anatomical claims** (Day 6) — not audited. These are basic anatomy, hard to get wrong, but a clinician should still review.
- **Cognitive restructuring claims** (Days 23–27) — not audited as clinical psychology. The CBT framings are standard, but a CBT therapist's review would catch any overcommitments.
- **Specific breath-physiology claims** (Day 6 of the arousal scale week, "long exhale shifts to parasympathetic state") — broadly true (vagal tone increases with extended exhale; HRV research supports this), so I didn't dig deeper.

---

## PASS 4 — Dependency and continuity check

### Issues found

**🟡 #7 — Recovery sequence on Day 37 references behaviors not yet introduced**

Day 37 ("After a bad sex moment") gives a four-step recovery sequence: don't catastrophize, don't withdraw, run recovery practice within 24 hours, check in with your partner. The "recovery practice" is described as "the same daily session you've been doing. Breath. Body awareness. Maybe a short meditation."

Problem: this assumes the user has a *specific* practice they recognize as "the daily session." The program does refer to daily practice from week 1 onward, but never explicitly names a "default daily session" that the user runs every day. By Day 37, depending on which sessions the user has actually done, "the daily session" might mean: extended exhale, body scan, light PFM, sensate focus, edging, stop-start, or some combination.

**Fix:** add a one-line clarification in Day 37: *"By 'recovery practice' I mean whichever short practice has become your usual one — the breath, the body scan, or both. If you don't have a default, default to extended exhale for five minutes."*

**🔵 #10 — Sensate focus / genital touching contradiction**

Day 11 (solo sensate focus): *"No genital touching during this exercise."*
Day 18s (longer solo work, solo path): *"Touch your body slowly, with attention. Including the genitals this time, lightly, but the focus is the whole body."*

These are reconcilable — Day 11 is pure sensate focus (rest-of-body discovery), Day 18s is longer integrated work that includes everything. But a careful listener will notice the apparent contradiction.

**Fix:** add one line to Day 18s: *"This is different from the sensate focus session in week 2, where genitals were excluded — that was about reopening the wider body. Here, we're integrating, so the genitals are in but not the focus."*

**🔵 #15 — Partnered path lacks "what if partner says no" content**

Day 18p (the conversation) acknowledges the partner-says-no possibility in one paragraph: *"If your partner says no, you're not stuck — you continue on the solo path, and you can revisit the conversation in a few weeks."*

But Days 19p and 20p (partnered sensate focus, partnered stop-start) assume the partner agreed. There's no real handling of "we tried, and it went badly" or "she said yes initially but doesn't want to do it now."

**This is a real gap** but is hard to fix without writing 2–3 additional sessions or branching the partnered path further. For v1, the existing handling is probably sufficient — the user can fall back to solo path content. Worth flagging as a future content addition based on beta feedback.

### No issues found

- Week 2 successfully builds on Week 1 (breath → arousal scale extends breath to arousal contexts).
- Week 4 cognitive content is appropriately set up by Week 1 (spectatoring) and Week 2 (thoughts during sex).
- Week 6 (recovery) successfully builds on Week 4 (catastrophic narrative concept).
- Week 8 maintenance plan correctly references practices established in weeks 1–3.
- The branching at Day 18 (partnered/solo) is internally consistent and converges cleanly at Day 21.

---

## PASS 5 — Tonal failure-mode check

### Issues found

**🟡 #5 — Day 24: putting a clever line in the user's mouth**

End of Day 24 (responsibility belief):
> *"If you have a partner, this reframe sometimes helps if you tell them about it. 'I've realized I've been treating your pleasure like it's my homework. I want to stop doing that. I'm not going to stop caring whether you have a good time — I'm going to stop treating it like my responsibility to deliver.' Most partners hear this as good news."*

Problem: this is a *very specific*, *somewhat clever* line. If a user takes the suggestion literally and uses it verbatim, two failure modes:
1. The line sounds rehearsed (because it is)
2. If their partner has heard the same line from another podcast/app/book, the magic is gone

Also: the metaphor "like it's my homework" is cute but might land oddly with a partner who hears it cold. Some men will say it; their partner will think "where did you get *that* phrase from?"

**Fix:** rephrase to suggestion, not script:
> *"If you have a partner, sharing this reframe with them sometimes helps. The shape of what to say: that you've realized you've been treating their pleasure as something you have to deliver, and that you want to stop doing that — not because you've stopped caring, but because the responsibility-frame was the thing making you anxious. Find your own words for it. Most partners hear something like this as good news."*

This guides without scripting.

**🔵 #9 — Day 47: substance-use mention may land judgmental**

> *"If alcohol or substance use is meaningfully present in your life — this program assumes basic sobriety. Heavy alcohol use, regular cannabis or other substance use, can affect sexual function in ways behavioral training doesn't override."*

The phrase "regular cannabis use" can land as judgmental for a user who, say, has a 1-2x/week cannabis routine and considers that normal/recreational. Specifically the word "regular" is doing a lot of work — it might mean "every day" or "every weekend," and the user might project either onto it.

**Suggested rewrite:**
> *"If alcohol or substance use is significantly affecting your daily life — daily drinking, frequent cannabis, or other substance use that's interfering with how you function — this program assumes you've stabilized that or are working on it elsewhere. Heavy use of any substance can affect sexual function in ways behavioral training doesn't override."*

The shift: from "regular" (which sounds like any-frequency moralizing) to "significantly affecting your daily life" (which is what we actually mean — clinical-impact use, not recreational).

**⚪ #14 — Day 45 ("The man you're becoming") aspirational tone**

Day 45 is the most aspirational session in the program — five paragraphs starting "A man who…" describing the trajectory. Some users may find it slightly self-help-y. But: the previous 44 days have earned this register, and the content is grounded in specific skills the user has actually built. I don't think this is a problem; flagging only because someone with very low tolerance for self-help language might react.

### No issues found

- No instances of moralizing about sex, performance, or anxiety.
- No condescension toward the user.
- No clinical-cold register that breaks the warmth.
- No moments where the voice tells the user "what you should feel" rather than "what some people feel."
- No religious framing creep.

The Variant D week 1 issue (NoFap-coded language risk) doesn't have a Variant A equivalent — there's no analogous failure mode that I found.

---

## PASS 7 — Inclusivity and assumption check

### Issues found

**🟡 #6 — Heterosexual / female-partner default throughout**

Specific instances (not exhaustive):

- **Day 18p:** *"the conversation"* — assumes the partner is not previously aware of PE work. Phrasing is mostly gender-neutral, but the example tone *"Sex has felt rushed to me lately"* defaults to a heterosexual-cis-coupled framing.
- **Day 19p (partnered sensate focus):** *"One person is the giver, one is the receiver."* — gender-neutral, good. But the "no genital touching, no breast touching" rule uses "breasts" without acknowledgment that for a male-male couple this rule would translate differently.
- **Day 20p (partnered stop-start):** *"penetration"* — defaults to penetrative sex with the user as the penetrator. For male-male couples, the user might be receptive, in which case the technique applies differently.
- **Day 27 (what partners actually want):** *"specifically, female partners of men with PE, since most of the research has been done with that population."* — at least acknowledges this. Good.
- **Day 53 (relationship maintenance):** generic "your partner" but framed around long-term cohabitating relationships.

**Realistic scope of fix:**

Variant A's content is built around the most common case — a male user with one female partner. Trying to handle all permutations (gay couples, bi users, trans users, non-monogamous users, etc.) would explode content scope and dilute the protocol.

**Pragmatic recommendation:**

Add a single 4–5 minute session — probably as part of Day 15 ("Where the work goes from here") or as a standalone "diversity note" — that explicitly says:

> *"This program was written with the most common case in mind: a man with one female partner. The skills generalize to any sexual context — solo, with a male partner, with multiple partners, in any configuration of relationship. Where I use specific gendered language or assume penetrative-sex-as-the-frame, translate it to your situation. The breath, the awareness, the cognitive work, the sensate focus principles — all of these apply regardless of partner gender or relationship structure. If you find specific sessions don't quite fit your context, take what's useful and skip what isn't."*

This is honest about scope without trying to retro-fit every session. Most users will find this acceptable.

**🔵 #12 — Singular-partner assumption**

Throughout the program, "your partner" is used in singular form. Polyamorous users with multiple partners, or users in an early-dating phase with multiple sexual contacts, may find this slightly off-fitting.

The fix is incorporated into the diversity note above. Single line: *"And — 'your partner' is shorthand throughout this program for whoever you're being sexual with. If you have multiple partners, the work applies in each relationship; you may find some partners are more interested in the partnered exercises than others."*

### Other observations

- **No assumptions about marital status.** Good.
- **No assumptions about age or life stage.** The Variant A content reads equally well for a 25-year-old or a 45-year-old.
- **No assumptions about religious/cultural background.** No religious framing slips through (this was the explicit failure mode for Variant D, and I checked Variant A specifically — no creep).
- **No appearance/body-shape assumptions.** Good.
- **No income/access assumptions.** "Set aside 30 minutes" and "find privacy" assume some life flexibility, but this is unavoidable for the protocol design.

---

## Recommended action sequence

**Priority 1 (do before audio generation):**
- Apply rewrites for #1, #2, #3, #4 (factual claims)
- Apply rewrite for #5 (the homework metaphor)
- Apply fix for #7 (Day 37 recovery practice clarification)
- Apply rewrite for #9 (substance-use phrasing)
- Apply minor rewrite for #11 (Day 9 median-of-men framing)

**Priority 2 (do before public launch but not blocking beta):**
- Add the diversity note (#6, #12)
- Apply fix for #10 (sensate focus / genital touching reconciliation)
- Decide whether to address #15 (partner-says-no path) or accept the gap for v1

**Priority 3 (revisit after voice generation):**
- Listen to weeks 7–8 in voice and decide if the register-shift (#8) needs adjustment
- Listen to closing patterns (#13) and decide if "Good work today" needs varying

**Priority 4 (note only, no action):**
- #14 (Day 45 aspirational tone) — listen and decide
- General observation: the content overall is in good shape. The factual issues are all in a single direction — slight overclaiming — which is a writer's tic worth knowing about, but no individual claim is dangerous.

---

## Rough word count diff if all priority 1 changes applied

The substantive rewrites (#1–5, 7, 9, 11) would add maybe ~150–200 words across the program (mostly because the rewrites are slightly longer than the originals — softening typically requires more words than overclaiming). Negligible impact on session durations.

If the diversity note is added (#6, #12) as a new ~600-word session, that's one additional session script and ~4 minutes of audio per voice.

Total new content if all changes accepted: ~750–800 words. About 1.5% of the existing Variant A inventory.
