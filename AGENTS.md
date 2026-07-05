# AGENTS.md — Handoff for the next coding agent

You are picking up a working **draft** of a commodity-fundamentals **root-cause knowledge graph +
symbolic reasoning + event system + ops CLI + web service**. Your job is to continue development
inside a company environment, primarily **wiring the system to read real research reports** and
turning them into knowledge. This file tells you exactly how to proceed and what you must not break.

---

## 0. 30-second orientation

- The knowledge is a graph of **neutral root causes** connected by **causal edges** (each edge carries a mechanism: polarity/lag/strength/condition). It lives as **YAML text** in `kg-mvp/data/`.
- A **symbolic engine** (`kg-mvp/propagate.py`) propagates ±1 shocks along the graph and produces explainable, time-bucketed conclusions. **The LLM never does this propagation.**
- **Events** (timestamped ±assignments to root causes) drive the graph; they come from news/data.
- Everything is **KG-as-code**: YAML is the source of truth, git is the approval system, CI is the gatekeeper.

## 1. Read before touching anything (in this order)

1. `METHODOLOGY.md` — the *why* and the **7 principles you must not violate** (§2 below is the enforceable summary).
2. `ENGINEERING.md` — architecture, stubs, how to run, the company-onboarding plan.
3. `kg-mvp/docs/SPEC.md` — data schema (nodes/edges/events), endpoint contracts, CI rules.
4. `kg-mvp/docs/RUNBOOK.md` — the exact commands.
5. Skim `kg-mvp/data/copper.yaml` — the reference graph (SHFE copper). This is what "good" looks like.

## 2. Ground rules (non-negotiable — violating these breaks the design)

1. **Knowledge lives in YAML.** Never hardcode graph facts (nodes/edges/events) in Python. To change knowledge, edit `kg-mvp/data/*.yaml`.
2. **Root causes are NEUTRAL state variables.** Never name a node with a direction word ("… surge", "… shortage", "… hike"). Names describe a *quantity*; the `direction` field explains what +/− mean.
3. **Edges store mechanism, news sets direction.** An edge's polarity is "source↑ → target↑/↓". The *direction of a real event* comes from the news and is injected as a ±1 shock — it is not baked into the graph.
4. **The symbolic engine does the transmission; the LLM does not.** `propagate.py` computes the chain deterministically. The LLM only (a) parses news/reports into events at the *entrance*, and (b) explains the *exit* using the full computed chain as prompt context. Never let the LLM "estimate the price impact" by free reasoning — that reintroduces hallucinated causality.
5. **Every change is a PR; AI edits require human review.** A human may edit YAML directly. Anything **you (the agent) produce must land in a review queue / PR and be approved by a human before it enters the graph or event log.** Never auto-merge AI-drafted knowledge.
6. **Do not adjudicate conflicts.** When bullish and bearish paths coexist, output both — do not collapse to one direction.
7. **CI must stay green.** Run `cd kg-mvp && python cli.py ci` before and after your changes. If you add structural knowledge (new root cause, new feedback loop), add/adjust a golden test in `ci_checks.py`.
8. **Company reports & real data are confidential — never commit them.** Put them under `reports/` (which you will gitignore, see §4.3). Keep secrets (API keys) in env vars / `.env` (gitignored), never in code or YAML.

## 3. Get it running & verify (do this first)

```bash
# backend engine + service deps
pip install networkx pyyaml fastapi "uvicorn[standard]"

# 1) sanity: the quality gate must pass
cd kg-mvp
python cli.py ci                    # expect: all checks pass, exit 0

# 2) try the reasoning
python cli.py morning --today 2026-07-06     # time-bucketed conclusion from active events
python cli.py advocate --stance bull         # counter-paths for a bullish view

# 3) web service (optional but recommended to see the graph)
cd ../service/frontend && npm install && npm run build
cd ../backend && python -m uvicorn app:app --port 8000   # open http://localhost:8000
```

If `cli.py ci` is not green on a clean pull, fix that before anything else — it is the contract.

## 4. YOUR PRIMARY MISSION: read real research reports → candidate knowledge

This is the biggest value lever. The pipeline scaffolding exists; the LLM call is a stub. Implement it.

### 4.1 The socket: `kg-mvp/pipeline_news_events.py :: llm_parse()`
Right now it returns `None` (so extraction falls back to keyword matching + human direction). Replace it with a real LLM call. **Contract:**

- **Input**: one news/report item `{date, title, text}` **plus the controlled vocabulary** = the list of existing root-cause node ids from the graph (get them from `build_graph.load(...)`).
- **Output**: zero or more **candidate events**, each: `{root_cause, direction (+1/-1), magnitude, window, quote, confidence}`.
  - `root_cause` **MUST be an exact existing node id** from the controlled vocabulary. This is the anti-hallucination guard.
  - `window` must be one of the known values (see `build_graph.LAG_MONTHS` or `待反转`/"until-reversed").
  - `quote` = the sentence in the report that justifies it (provenance is mandatory).
- **Unmappable content → the UNMAPPED queue** (`out/unattributed.yaml`), which is the **new-root-cause candidate** signal. Do not force-fit a report into a wrong node.
- **Everything lands in the review queue** (`out/review_queue.yaml`) or unmapped queue — **never written straight to `data/copper_events.yaml`.** A human promotes items with `python cli.py approve`. (See `approve_events.py`.)

### 4.2 Config: env-based LLM (no hardcoded keys)
- Read `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` from environment.
- Add a `.env.example` documenting these; load `.env` (gitignored). If no key is set, `llm_parse()` must degrade gracefully (return None, keyword path still works).

### 4.3 Report intake + data isolation
- Create `reports/` at repo root for real reports, and add `reports/` to `.gitignore` (company docs must not be committed).
- Add a way to run extraction over a report file (extend `cli.py ingest-news` or add `ingest-reports`) that reads from `reports/`, calls `llm_parse`, and fills the review/unmapped queues.

### 4.4 Second lever: report-diff → candidate edges
- Beyond events, an agent can compare "mechanisms a report describes" vs "edges already in the graph", and draft **candidate edges** for the missing ones (with the report citation in `evidence`). These are **PRs to `data/copper.yaml`**, reviewed by an analyst — never auto-applied. Follow the edge schema in SPEC §4.2.

### 4.5 Validate quality before scaling
- Run 5–10 real reports through the pipeline. Eyeball the review queue: are root-cause mappings correct? Are directions sane? Tune the prompt. Report rough precision to the human. Do **not** flip anything to auto-approve.

## 5. Extension-point map (stubs → what to wire)

| Location | Now (stub) | Wire to |
|---|---|---|
| `pipeline_news_events.llm_parse()` | returns None | real LLM: report/news → candidate events (contract in §4.1) |
| `data/feeds/*.csv|jsonl` | made-up sample data | real data-source APIs (Wind / SMM / customs / exchanges); keep the CSV/JSONL column contract or add a `fetch_indicators()` adapter |
| event storage | YAML files (`data/*_events.yaml`) | fine for now; move to SQLite/Postgres only when volume demands (don't do this prematurely) |
| `create_pr()` for the UI editor | not built yet | local `gh` / company GitLab MR / intranet git — design is in `.lavish/editor-design.html` |

## 6. How to change knowledge safely

- **Add an event**: `cli.py ingest-data` / `ingest-news` → review queue → `cli.py approve`. Never edit the events YAML by hand for machine-sourced events.
- **Add / modify a root cause or edge**: edit `kg-mvp/data/copper.yaml` per SPEC §4 (keep names neutral, fill `direction`/`temporal` for root causes; fill five fields + `rationale` for edges) → `python cli.py ci` → open a PR.
- **Add a new commodity**: create `data/<x>.yaml` + `data/<x>_events.yaml`, then register the commodity in the module-level mappings. ⚠️ **Known rough edge**: the `{commodity → (yaml_path, target_node)}` mapping is currently duplicated across several modules (`morning_report.py`, `conflict_dashboard.py`, `devils_advocate.py`, `detect_anomaly.py`, `refresh_themes.py`, `scan_reviews.py`, `pipeline_*_events.py`, and `service/backend/app.py`). Either update all of them, or (better) centralize into one config module — a worthwhile small refactor. Keep shared root causes (e.g. USD index, crude) type-consistent across commodities; CI checks this.

## 7. Out of scope unless the human asks

- Don't replace YAML with a database yet.
- Don't build the full editor UI without confirming the design decisions (see `.lavish/editor-design.html`, decisions E1–E4).
- Don't auto-merge any AI-generated change.
- Don't commit anything under `reports/` or any real company data.

## 8. File index (where to look)

| File | Purpose |
|---|---|
| `kg-mvp/data/copper.yaml` | reference graph (root causes + edges + themes) |
| `kg-mvp/data/copper_events.yaml` | event log |
| `kg-mvp/build_graph.py` | YAML → networkx + validation; `LAG_MONTHS` window vocab |
| `kg-mvp/propagate.py` | QPN symbolic propagation (the reasoning engine) |
| `kg-mvp/events_lib.py` | event read/write + active-event filter (`待反转` semantics) |
| `kg-mvp/pipeline_news_events.py` | **← your main file: `llm_parse()` stub** |
| `kg-mvp/pipeline_data_events.py` | data → z-score events |
| `kg-mvp/approve_events.py` | human promotes queued events |
| `kg-mvp/cli.py` | unified entry for all ops commands |
| `kg-mvp/ci_checks.py` | CI quality gate (schema + golden tests) |
| `service/backend/app.py` | FastAPI (4 endpoints) |
| `service/frontend/` | React + Vite + React Flow UI |

## 9. Open decisions the human still owns (don't decide these yourself)

- Editor scope & PR mechanism (decisions E1–E4 in `.lavish/editor-design.html`).
- Which real data sources to connect first.
- Whether the company repo stays public/GitHub or moves to private/GitLab (affects `create_pr()` and data isolation).

---

**Golden rule if unsure**: the LLM drafts, the engine computes, the human approves, git records. Keep those four roles separate and you cannot go badly wrong.
