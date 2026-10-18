# MiroFish India Monitor

A real-time viral misinformation detection and moderation dashboard for India-focused social media content, built as an extension of **MiroFish**, a multi-agent AI prediction engine.

MiroFish extracts seed information from the real world (breaking news, policy drafts, financial signals) and builds a parallel digital world where thousands of agents with independent personalities, long-term memory and behavioral logic interact. This extension applies that engine to misinformation: it ingests viral posts, verifies claims against official fact-check sources, simulates how unverified claims might spread, and gives human analysts a dashboard to review and act.

The core simulation engine is powered by [OASIS](https://github.com/camel-ai/oasis) (Open Agent Social Interaction Simulations) from the CAMEL-AI team.

---

## Features

- **Live ingestion** from X (Twitter), Instagram, YouTube, Google News India, and Reddit RSS
- **Verification pipeline** with specialist agents, grounded in official PIB Fact Check sources
- **Urgency routing** that triages by harm, uncertainty, spread and complexity (never by a truth probability)
- **Spread-graph analytics** in Neo4j (burst detection, PageRank)
- **OASIS simulations** that forecast the spread of high-risk unverified claims
- **ML fake-news classifier** (TF-IDF + Logistic Regression) as a supporting signal
- **Human-in-the-loop analyst console** with review, evidence explorer and audit log

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND (Vue 3 + Vite)                   │
│                 http://localhost:3000/console                │
│  Live Monitor · Verification Queue · Claim Investigation     │
│  Evidence Explorer · Simulations · Moderation Review         │
│  Audit Log · Settings                                        │
└──────────────────────────────────────────────────────────────┘
                              │  API proxy (/api)
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                  BACKEND (Flask + Python 3.11)               │
│                    http://localhost:5001                     │
│  /api/monitor/ingest   live collect → gate → route → verify  │
│  /api/monitor/queue    sightings / jobs / reviews / actions  │
│  /api/monitor/approve  human-approved platform report        │
│  /api/graph/*          GraphRAG construction (Zep Cloud)     │
│  /api/simulation/*     OASIS Twitter/Reddit simulation       │
│  /api/report/*         ReportAgent evidence pack             │
│  /health               service health check                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Agents

| Agent | Role | Trigger |
|---|---|---|
| OASIS simulation agents | Forecast spread of unverified claims in a simulated Twitter/Reddit world | Only when `POST /api/simulation/start` is called |
| `text_verifier` | Base claim extraction and verification | Every post |
| `image_forensics` | Image manipulation detection | Image / mixed content |
| `video_forensics` | Video deepfake detection | Video / mixed content |
| `audio_transcriber` | Audio transcription | Audio content |
| `source_credibility` | Source trustworthiness scoring | Evidence uncertainty ≥ 0.5 |
| `multilingual_retriever` | Non-English claim verification | Language ≠ English |
| `evidence_synthesizer` | Multi-evidence aggregation | Uncertainty ≥ 0.6 or complexity ≥ 0.6 |
| `ml_classifier` | ML fake-probability score (supports, never decides) | Every routed post |
| `ReportAgent` | Post-simulation evidence pack | After simulation completes (COMPLETED / STOPPED) |

---

## Routing and Verification Logic

The moderation router computes a **verification urgency score**, not a truth probability:

```
score = (0.45 × harm + 0.25 × uncertainty + 0.20 × spread + 0.10 × complexity) / total
```

| Tier | Score |
|---|---|
| low | < 0.35 |
| normal | 0.35 – 0.60 |
| high | 0.60 – 0.80 |
| urgent | ≥ 0.80 |

Virality never implies guilt. It only sets triage speed.

**Verdict rules (conservative)**

- `confirmed_fake` requires an official PIB fact-check citation match (score ≥ 0.3)
- `unverified` is the default when no official citation exists; human review is required
- The ML classifier supports but never decides alone

**Event trigger:** a simulation and report run only when tier ∈ {high, urgent} **and** a burst is detected **and** verdict == `confirmed_fake`.

---

## Fake-News Classifier

Trained on `master_fake_real_clean.csv` (68,173 rows drawn from LIAR, ISOT, TheOnion, India_MythFacts and others).

| Metric | Value |
|---|---|
| Training rows | 54,002 (24,205 fake / 29,797 real) |
| Test accuracy | 0.8981 |
| Precision (fake) | 0.9003 |
| Recall (fake) | 0.8688 |
| F1 (fake) | 0.8843 |
| F1 (real) | 0.9089 |

Model: TF-IDF (word 1–2 grams) + Logistic Regression, saved in `backend/models/fake_news_master/`.

---

## Project Stages

| Stage | Component |
|---|---|
| 0 | Baseline freeze and compliance scope |
| 1 | Connectors (X / Instagram / YouTube / Google News RSS) → RoutingInput |
| 2 | Neo4j spread-graph and analytics (burst detection, PageRank) |
| 3 | Realtime scheduler, RSS/webhook quota reduction |
| 4 | Verification workers, PIB ground truth, Web-Writer |
| 5 | Event bus (urgent + burst + fake → simulation trigger) |
| 6 | Reviewer dashboard, runner wiring, monitor API |
| 7 | Live dry-run with real APIs |
| 8 | Real-time social scraping (Reddit RSS, Google News) |
| 9 | ML fake-news classifier |

Per-stage documentation lives in `docs/india-monitoring/`.

---

## Getting Started

### Prerequisites

- Python 3.11–3.12
- Node.js 18+
- Neo4j (optional, for spread-graph persistence)

### Backend

```bash
cd backend
cp .env.example .env    # fill in LLM_API_KEY, ZEP_API_KEY, NEO4J_PASSWORD, etc.
python -m pip install -r requirements.txt
python run.py
```

Backend runs at http://localhost:5001.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Console runs at http://localhost:3000/console.

### Docker

Docker and Docker Compose configuration is included for containerized runs.

---

## Usage

1. Open `/console/settings` and turn demo mode **off** for live data, or leave it **on** to use dataset fixtures.
2. Go to **Live Monitor** and click **Fetch live feed**.
3. Review incoming items with their accounts, tiers and urgency meters. Click **Open source** to view the original article or post.
4. Click **Investigate** to see the urgency rationale, evidence and verdict options.
5. Submit a human verdict in **Moderation Review**.
6. Check **Audit Log** for the record of all actions.

### Dataset scripts

```bash
cd backend
python scripts/train_fake_news_master.py   # train on your downloaded dataset
python scripts/hf_ifnd_test.py             # test on the HuggingFace IFND dataset
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask, Flask-CORS |
| Simulation | OASIS (camel-ai, camel-oasis) |
| Graph / Memory | Zep Cloud (GraphRAG), Neo4j (spread-graph) |
| LLM | OpenAI-compatible API (Qwen-plus via Bailian) |
| Frontend | Vue 3, Vite, Vue Router, Axios |
| ML | scikit-learn (TF-IDF + Logistic Regression) |
| Data | Pandas, HuggingFace datasets |
| Container | Docker, Docker Compose |

---

## Project Structure

```
backend/
├── app/
│   ├── api/                 graph.py, simulation.py, report.py, monitor.py
│   ├── services/
│   │   ├── connectors/      X/IG/YT clients, scoring, collector
│   │   ├── spread_graph/    Neo4j schema, analytics, store
│   │   ├── realtime/        quota, webhooks, scheduler, server
│   │   ├── verification/    PIB client, web-writer, workers, model_verifier
│   │   ├── eventbus/        bus, wiring, monitor_store
│   │   └── moderation/      router.py (urgency routing)
│   └── config.py
├── models/fake_news_master/ trained classifier artifact
├── scripts/                 train_fake_news_master.py, train_fake_news_improved.py,
│                            stage7_dryrun.py, check_sightings.py
├── run.py                   Flask entry point
├── pyproject.toml
└── requirements.txt

frontend/
├── src/
│   ├── console/
│   │   ├── AppShell.vue
│   │   ├── views/           Overview, LiveMonitor, VerifyQueue, Investigation,
│   │   │                    EvidenceExplorer, Simulations, Review, AuditLog, Settings
│   │   ├── components/      MfIcon, MfBadge, UrgencyMeter, EmptyState,
│   │   │                    ConfirmDialog, DemoBanner
│   │   ├── fixtures/        demoClaims.js
│   │   ├── api.js, connection.js, demoMode.js, analystStore.js, toasts.js
│   ├── api/index.js         axios client
│   ├── router/index.js      /console routes
│   └── main.js
├── index.html
├── package.json
└── vite.config.js

docs/india-monitoring/       STAGE0–STAGE9 documentation
```

---

## Safety and Compliance

- **Report-only mode:** `ACTION_MODE=report_only` is enforced; no auto-blocking of third-party accounts.
- **Official APIs only:** X API v2, Instagram Graph API, YouTube Data API. No password scraping.
- **Public pages only:** Web-Writer reads PIB and ministry pages; no login-wall scraping.
- **PII minimization:** stores post IDs and public metrics, not private messages.
- **Human-in-the-loop:** all consequential actions require reviewer approval.
- **IT Rules 2021 / DPDP Act:** virality is not guilt; an audit log is maintained.

---

## Known Limitations

- X, Instagram and YouTube require official API tokens (placeholders in `.env`); Reddit RSS and Google News RSS work without keys.
- PIB Fact Check has no public RSS feed, so ground truth falls back to verdict-pattern Google News headlines.
- YouTube RSS is intermittently bot-gated and is skipped gracefully.
- The classifier is trained on article-length text, so short social claims are noisier. It supports decisions but never makes them.
- All enforcement is report-only and needs human approval.

---

## License

AGPL-3.0, the same as the original MiroFish project. Strategic support and incubation from Shanda Group.

## Acknowledgements

- [OASIS](https://github.com/camel-ai/oasis) by the CAMEL-AI team
- Zep Cloud for GraphRAG memory
- Datasets: LIAR, ISOT, TheOnion, India_MythFacts, HuggingFace IFND
