# Engineering + Company-Environment Onboarding

> Handoff doc 2/2. How the methodology (`METHODOLOGY.md`) becomes running code, and how this draft
> repo can quickly become useful once inside the company and paired with real research reports.
> Interactive version: `.lavish/02-engineering-en.html` (open with `npx -y lavish-axi <file>`).

## Where we are

An end-to-end runnable draft — graph body (SHFE copper 41 nodes / 55 edges, plus palm oil and olive
oil) + reasoning engine + event system + ops CLI + CI + a web service (FastAPI + React Flow), already
on GitHub, CI green, runs locally. **What's missing is the "real data / real reports" integration —
which is exactly what to do inside the company.**

## 0. At a glance

```
Source of truth (git):  data/*.yaml  (graph body + event log)
        │
Engine (kg-mvp, pure Python):  build_graph(networkx) · propagate(QPN) · events_lib(active filter)
        │
Consumption:  CLI (ops)  ·  web service (FastAPI + React Flow)  ·  UI editor → PR
Gatekeeper:   CI (schema + golden + event checks) on every YAML change
Company wiring (to do):  LLM parses reports → candidate events/edges ;  real data-source API → z-score events
```

## 1. Repository structure

```
fundamental_research/            git repo (GitHub: RioAraki/fundamental_research)
├── kg-mvp/                       engine + knowledge + ops
│   ├── data/*.yaml               ★ source of truth: graph body + event log (only human-reviewed layer)
│   ├── data/feeds/               data/news inputs (stubs now; swap for real sources in company)
│   ├── build_graph.py            YAML -> networkx + validation
│   ├── propagate.py              QPN symbolic propagation (reasoning)
│   ├── events_lib.py             event read/write + active-event filter
│   ├── pipeline_data_events.py   data-type event pipeline (z-score)
│   ├── pipeline_news_events.py   news-type pipeline (contains llm_parse stub <- wire in company)
│   ├── cli.py                    unified entry (ingest / morning / conflict / advocate / anomaly / ci)
│   ├── ci_checks.py              CI quality gate (schema + golden + event checks)
│   └── docs/SPEC.md · RUNBOOK.md engineering spec + ops manual
├── service/  backend (FastAPI, 4 endpoints) + frontend (React + Vite + React Flow)
├── .github/workflows/ci.yml      GitHub Actions: quality gate on every YAML change
├── METHODOLOGY.md · ENGINEERING.md   handoff docs
└── .lavish/                      design / handoff pages
```

## 2. Three tiers: engine / consumption / gatekeeper

| Tier | What | Key point |
|---|---|---|
| Engine (kg-mvp) | pure Python, commodity-agnostic: build_graph + propagate + events_lib | a new commodity is just one more YAML file, zero code change |
| Consumption: CLI | ops cadence (daily ingest/morning, weekly themes, monthly shelf-life, close-of-day anomaly) | can run unattended; also the agent's interface |
| Consumption: web service | FastAPI 4 endpoints + React Flow frontend | interactive graph + scenario reasoning; two commands to start locally |
| Gatekeeper: CI | schema + golden tests + event checks + cross-commodity consistency | runs on every PR, prevents breaking the graph |

## 3. 🏢 Company-environment onboarding (the focus)

### A. To add before bringing it in (make it "plug-and-play")

| Item | What to do | Why |
|---|---|---|
| **Data isolation** | add a `reports/` intake folder and gitignore it; company reports/real data **must never enter this (public) repo**; or convert to a private repo on arrival | reports carry copyright/confidentiality; code and data must be separated |
| **LLM integration point ready** | add `.env.example` (LLM_API_KEY/BASE_URL/MODEL); write the `llm_parse()` stub as a "read env var → call" skeleton, working once a key is filled in | report → event/edge extraction is the biggest value lever; have the interface ready |
| **Data-source adapter** | abstract the feed reader into `fetch_indicators()`; reads CSV now, implement Wind/SMM at the company | swapping the data source shouldn't touch the pipeline |
| **Onboarding doc** | a one-page `docs/ONBOARDING.md`: how a colleague installs, starts the service, adds an event | a non-technical colleague can run it themselves on day one |
| **PR mechanism abstraction** | make `create_pr()` a function (swappable: local gh / company GitLab / intranet git) | the company may not use GitHub — keep the interface open |

### B. Rollout order inside the company (make it "useful fast")

| When | Action | Output |
|---|---|---|
| **Day 1** | install, start the service, demo the existing copper graph to analysts/traders, build intuition, collect first reactions | alignment + first batch of edits |
| **Day 1-2** | wire in a real LLM, take 5-10 real reports through "report → candidate events/edges → review queue", inspect extraction quality | validate whether the core lever holds |
| **Week 1** | analysts review copper's 55 edges (calibrate direction/strength/lag with real knowledge) + add the root causes the firm cares about; batch-diff reports to fill missing edges | the first "company version" of a trusted graph |
| **Week 1-2** | wire 1-2 real data sources (replace feed stubs), automate data-type events; ship the UI editor so non-technical colleagues log events | the graph starts to "live" (updated daily) |
| **Ongoing** | backtest-calibrate edge strengths (methanol-report method); extend to more commodities (each is one more YAML) | from draft to production |

### C. Reports are the firm's biggest asset — how to use them

- **The controlled vocabulary is the anchor**: the LLM can only map report content to **existing root causes** (anti-hallucination); anything unmappable goes to an "unmapped queue" = a **new root-cause candidate** (the report tells you what the graph is missing).
- **Report diff to fill edges**: an agent compares "the mechanism the report describes vs edges already in the graph"; missing ones become candidate-edge PRs (with citation) — more efficient than reading news, since a report is already a structured view.
- **Historical reports serve double duty**: ① seeds for cold-starting graph expansion; ② corpus for backtest calibration (report view vs subsequent price action).
- **Human review always gates entry**: the LLM only drafts candidates → review queue / PR → analyst approves before it enters the graph.

## 4. Current stubs & extension points (already marked in code)

| Location | Now | Replace with (company) |
|---|---|---|
| `pipeline_news_events.llm_parse()` | returns None (direction left to human) | a real LLM: report/news → {root cause, direction, magnitude, window, citation} |
| `data/feeds/*.csv\|jsonl` | made-up sample data | real data-source APIs (Wind/SMM/customs/exchanges) |
| editor `create_pr()` (to be built) | — | local gh / company GitLab MR / intranet git |
| event storage | YAML files | SQLite/Postgres once volume grows (interface planned) |

## 5. How to run (quick reference)

```bash
# environment
pip install networkx pyyaml fastapi "uvicorn[standard]"   # backend
cd service/frontend && npm install                          # frontend (first time)

# web service (single process, recommended)
cd service/frontend && npm run build
cd ../backend && python -m uvicorn app:app --port 8000      # open http://localhost:8000

# ops CLI (in kg-mvp/)
python cli.py ci                      # quality gate (run after editing edges)
python cli.py morning --today ...     # morning report (time-bucketed conclusion)
python cli.py advocate --stance bull  # counter-paths
python cli.py ingest-news --today ... # news -> review queue
```

See `kg-mvp/docs/RUNBOOK.md` and `service/README.md` for details.
