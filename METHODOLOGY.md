# Commodity Fundamentals Root-Cause Knowledge Graph — Methodology

> Handoff doc 1/2. Covers the **why** (methodology). The **how (code)** lives in `ENGINEERING.md`.
> Interactive version: `.lavish/01-methodology-en.html` (open with `npx -y lavish-axi <file>`).

## In one sentence

We do **not** chase "end-to-end AI price prediction." Instead we make the analyst's causal
framework explicit as a **root-cause graph with direction / lag / strength**; a **symbolic engine
deterministically computes the full transmission chain, then hands the entire chain to an LLM to
interpret** — the LLM reads the entrance (parses events) and explains the exit, seeing the whole
reasoning process but never doing the propagation itself. The graph is an asset, the reasoning is
explainable, and the knowledge is collaboratively maintainable.

## 0. At a glance (three layers → engine → LLM)

```
Real world (news / data)
        │
        ▼
⚡ Event layer (fast)        one timestamped ±assignment to a root cause
        │ activates (inject ±1 shock)
        ▼
🧱 Root-cause layer (slow)   neutral root causes + intermediate nodes + causal edges  = the graph (git)
        │ provides structure           🔥 Theme layer (medium): attention tag on nodes, tunes pricing weight
        ▼
QPN symbolic engine          deterministic propagation (sign × strength × lag), conflicts NOT adjudicated
        │
        ▼
Full derivation chain  ──(as prompt)──▶  LLM (reads entrance / explains exit, never propagates)
        │
        ▼
Time-bucketed conclusion (0-1 / 1-6 / 6+ mo) + citable transmission paths
```

## 1. Seven core principles (not to be casually overturned)

| # | Principle | Why |
|---|---|---|
| 1 | **KG-as-code**: the single source of truth is YAML text in git; the graph DB / pages are regenerable artifacts | diff / rollback / blame / PR review; same flow as analysts writing docs |
| 2 | **Neutral root causes**: a root cause is a neutral state variable (e.g. "India import tariff"), its name has no direction word; a `direction` field explains +/− semantics | the same root cause moves both ways (tariff up/down); baking in a direction misses half the moves |
| 3 | **Graph stores mechanism, news sets direction**: an edge's polarity is the mechanism (source↑ → what happens to target); events enter as ±1 shocks | mechanism is stable (expert-maintained), direction is time-varying (news-driven) — keep them separate |
| 4 | **Three-layer ontology**: root cause / theme / event | separating mechanism, attention, observation (three time scales) is what makes it coherent |
| 5 | **Do not adjudicate conflicts**: output bullish vs bearish paths side by side; action semantics = stand aside during conflict + give the resolving signal | the conflict itself is a research signal; forcing one direction throws away information |
| 6 | **Engine computes transmission, the full chain is fed to the LLM**: propagation is executed deterministically by the symbolic engine (the LLM does NOT reason it out — avoiding hallucinated paths); but the computed **full derivation chain (each step's direction/lag/strength/condition) is passed to the LLM as part of the prompt**, so the LLM sees and can cite the entire chain while reading the entrance and explaining the exit | an LLM confuses correlation for causation and hallucinates paths, so it must not do the propagation; seeing the full chain lets it give a solid, traceable interpretation rather than guessing from the two ends |
| 7 | **Humans edit directly, AI edits need human review**: every change is a PR; a human may edit and submit directly, while any AI-drafted change must be reviewed by a human before it merges — PR review is the approval gate | no need to invent an approval system; git already has diff/rollback/history/CI; AI only drafts, humans decide |

## 2. Three-layer ontology: root cause / theme / event

**One-line test: strip the time and direction out of a news sentence; the noun that remains is the root cause.**

| Layer | Definition | Time scale | Stored in | Examples |
|---|---|---|---|---|
| 🧱 Root cause | a measurable, persistent, neutral state variable; a graph node (incl. intermediate transmission nodes) | years-decades | YAML graph | mine-supply disruption rate, India import tariff, property completion activity |
| ⚡ Event | one timestamped ± assignment to a root cause (from news/data) | hours-weeks | YAML event log | "2025.9 Grasberg accident" = mine disruption +1 |
| 🔥 Theme | the market-attention state of one/several root causes over a period; a tag on the node | months-years | a field on the node | "AI compute build-out", "property-chain collapse (dormant)" |

- **Root-cause reversion type (5 kinds)** — how it returns to baseline after a shock, which sets the *end* of an event's impact window: fast-reset (monthly-report surprise) / event-recovered (a strike) / state-held (an export ban, "until reversed") / trend-accumulating (tree age, never returns) / seasonal.
- **Why the theme is its own layer**: the same "completions −20%" caused a big drop in 2021 (theme active) but no reaction in 2025 (dormant) — the mechanism didn't change, what changed is whether the market is looking. Theme = a pricing-weight multiplier; dormant means discounted, not deleted.

### Confusing examples (the best way to tell the three layers apart)

| You'll hear | It is actually | Why it's confusing / correct decomposition |
|---|---|---|
| "Inventory rose again" | ⚡ Event | "inventory" itself is a **root cause (node)**; "it rose X kt this week" is the **event**; "the restocking cycle" is a **theme** — same word on all three layers |
| "The Fed hiked" | ⚡ Event | root cause is **"Fed policy stance"** (there's always a current stance); "this hike" is one +1 assignment |
| "Grasberg had an accident" | ⚡ Event | sounds like a "cause" but is one timestamped observation; root cause is **"mine-supply disruption rate"** |
| "Indonesia banned exports" | ⚡ Event (+1) | root cause is **"Indonesia export-restriction intensity"** (neutral); the ban is +1, the later flush-out is a separate −1 |
| "AI data-center demand" | 🔥 Theme (not a root cause) | the name stuffs a narrative into naming; the root cause is the neutral **"data-center / compute infrastructure demand"** (existed in 2015, will exist after AI cools); "AI compute" is a theme tag on it |
| "It's a supply-deficit market now" | 🔥 Theme | maps to **no single node** — a story woven from several root causes (mine disruption + zero TC + grade decline); theme:root-cause = many-to-many |
| "Grid investment is strong" | 🧱 Root cause (a reading) | the **current level** of "China grid investment" (slow, monthly reading); "State Grid announced +18% annual plan" is the event |

**Mnemonic**: can ask "what is its *value right now*" → root cause; a sentence with a *timestamp and direction* → event; "the market is all trading X lately" → theme.

## 3. Reasoning: QPN symbolic propagation

On a signed (±) causal graph, propagate from the event node along paths: **signs multiply (in series),
strengths multiply (weak edges decay), lags accumulate**; loops are handled by "no revisiting within a
path + return-to-source recorded as a feedback loop." Each computed path is a **derivation chain the
LLM can cite**.

- **Conflict handling**: bullish and bearish arriving at the same node → do not adjudicate; output both sides + strengths; conflict = stand aside, await the resolving signal.
- **Lag → time buckets**: bucket by cumulative lag into 0-1 / 1-6 / 6+ mo and sum each — answering "bearish near-term but bullish long-term".
- **Explainable**: every conclusion = a full chain (direction/lag/strength/condition); click a node for the bull/bear verdict, click an edge for "why this strength".

**An edge has only two kinds**: same-direction (+) = source up → target up; opposite (−) = source up → target down.
Walking the chain, track whether each node actually goes up or down:

```
start  Drought ↑
  │ opposite(−): drought vs yield are opposite → yield DOWN
  ▼    Yield ↓
  │ same(+): yield & output move together → output DOWN
  ▼    Output ↓
  │ same(+): output & inventory move together → inventory DOWN
  ▼    Inventory ↓
  │ opposite(−): inventory vs price are opposite → price UP
  ▼    Price ↑     ⇒ Drought↑ ultimately drives Price↑ = bullish
```

**Why does "some +, some −" end up +?** We are not adding signs, we are multiplying them
("negative × negative = positive"): a chain with an **even number of opposite(−) edges is net
same-direction; an odd number is net opposite**. This chain has **2 opposite edges** (drought→yield,
inventory→price); the two cancel → net same-direction, so "drought up" becomes "price up".
`(−)×(+)×(+)×(−)=+` is just shorthand for "count the minus signs".

## 4. Root cause = qualitative, event = quantitative (quantifying is hard — don't pretend it's automatic)

The **qualitative part (the graph)** is relatively stable and accumulable: where a root cause transmits,
through which nodes, in what direction — domain knowledge, expert-maintained. **The hard part is
quantifying** — "how big is this move." Honestly, two cases with vastly different difficulty:

| Case | How to quantify | Coverage / difficulty |
|---|---|---|
| A few periodic series with **both a number AND a market expectation** (MPOB stocks, social inventory, TC) | z-score = (actual − market expectation) ÷ std-dev of historical surprises; magnitude is an objective number | covers only a **small subset**; requires having the "market expectation" figure (survey, or historical-mean approx) — **not always available** |
| The **vast majority of events** (policy / shocks / strikes / report views) | no clean numeric surprise; magnitude can only be a **manual strong/medium/weak judgment by the analyst** | subjective, experience-driven — the **most human-dependent, hardest link**; we do not pretend it can be automated |

- **Stated honestly**: the z-score is a "compute-it-if-you-can" bonus (a few periodic series), **not a general capability**; quantifying event magnitude currently **relies mainly on manual analyst input**, a known hard bone, to be calibrated gradually via historical backtesting, not in one step.
- Each root cause's **monitoring signals** (news keywords + data sources) are a checklist of "what to look at, where to find it" that **lowers the cost of the manual judgment** — but the judgment itself is still human.
- The graph does not become useless because it "can't give a precise number" — it first makes the **direction and structure** (qualitative) clear and leaves the magnitude for a human; that alone beats "guessing causal chains off the top of one's head".

## 5. How the graph helps people find blind spots (the core value)

Human attention is limited, memory fades, and we tend to see only one side. The graph doesn't.

### ① Dormant-zone sweep — cures "I know the mechanism, but I'm not watching it" (attention blind spot, most valuable)
**How it works**: a scheduled job (e.g. weekly) scans root causes behind every `status=dormant` theme →
takes the current reading → computes its historical percentile → **if the reading is at an extreme
percentile (e.g. >P90 / <P10) yet the root cause has near-zero recent events** → flags "fundamentals
building potential energy while neither the market nor you is watching" → pins to top of the report.

*Example*: the "property completion activity" theme went dormant after 2023. In some month of 2026,
completions recover to the top of their 5-year range (P92), but nobody trades the property logic and
related news is near zero. The sweep surfaces: "⚠️ completions at a 5-year high yet theme dormant;
mechanism completions↑→end copper demand↑ may be underpriced — review whether to reactivate." The
graph remembers, for you, something you set down two years ago that may now matter.

### ② Counter-paths — cures "I only thought of one side" (path blind spot / devil's advocate)
**How it works**: the analyst states a view (e.g. "bullish SHFE copper") → the system propagates and
picks out all paths pointing **opposite to your view** (active-event-driven first, then structural) →
each annotated with chain, strength, lag, **preconditions and the verifying signal**. Subtext: these
are what your view must overcome to hold.

*Example*: you write "2026 supply deficit, bullish copper". The system auto-lists counter-paths:
- [bear 0.6] sulfuric-acid price↑ → smelter margin↑ → cuts don't materialize → refined supply doesn't shrink (precondition: by-product revenue stays high; verify: SMM monthly refined output);
- [bear 0.66] US tariff exemption → COMEX premium collapses → inventory flows back → LME under pressure (verify: COMEX-LME spread).

→ Forces you, before concluding bullish, to answer "why don't these beat the deficit logic?" The view becomes testable, not wishful.

### ③ Edge shelf-life + theme pricing-death — cures "I assumed it still works" (staleness blind spot)
**Two sub-mechanisms**:
- **Edge shelf-life**: every edge carries `review.last` (last human confirmation); a monthly scan flags edges past due (>12 mo un-reviewed) → remind analyst to recheck direction/strength.
- **Theme pricing-death**: for an active theme, if events are **still occurring** but price **sensitivity approaches 0** (event study: on same-direction-event days, price no longer reacts) → judge "fully priced in" → recommend downgrading the theme to dormant.

*Example (shelf-life)*: the edge "completions → end copper demand" was "strong" in the 2010s, now
"medium" as property's share fell; if `review.last` is stuck at 2024 and >12 mo un-reviewed by 2026 →
"this edge hasn't been reviewed in 2 years, confirm the strength".
*Example (pricing-death)*: in 2025 the "Section 232 tariff" theme first made COMEX swing on every
headline; later tariff news kept coming but price barely reacted → sensitivity ≈ 0 → recommend
downgrading (market has digested it), stop trading it as an active narrative.
