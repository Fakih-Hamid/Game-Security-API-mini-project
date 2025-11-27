# Game Security API

Demonstration of an anti-cheat monitoring platform concept that ingests gameplay telemetry, analyzes emerging threats, and surfaces actionable insights for security analysts.

## Highlights

- **RESTful Flask API** with JWT-secured endpoints for security, player, and analytics workloads.
- **SQLite + SQLAlchemy** storage seeded with realistic data: 50 players, 1,050 sessions, and dozens of events.
- **Signal engines** for anomaly detection, log analytics, and composite risk scoring.
- **Production touches**: rate limiting, input validation, CORS controls, structured logging, and Docker packaging.
- **Pytest suite** covering core routes and anomaly detection logic.

## Project Structure

```
game-security-api/
├── app/
│   ├── __init__.py
│   ├── routes/
│   ├── models/
│   ├── services/
│   └── utils/
├── tests/
├── docker/
├── requirements.txt
├── run.py
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- pip
- (Optional) Docker Desktop

### Local Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export FLASK_APP=run.py
python run.py
```

The API boots on `http://127.0.0.1:5000`. A SQLite database is created under `instance/game_security.db` with seeded telemetry.

### Authentication

Generate a JWT via the built-in service credentials:

```bash
curl -X POST http://127.0.0.1:5000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "security_console", "password": "letmein123"}'
```

Attach the returned token to every request using `Authorization: Bearer <token>`.

## API Reference

### Security

- `POST /api/security/scan-log` — ingest raw gameplay logs and flag suspicious activity.
- `GET /api/security/player-risk/<player_id>` — compute a 0–100 composite risk score.
- `POST /api/security/report` — manually file a security event.
- `GET /api/security/dashboard` — aggregate totals, KPIs, and recent escalations.

### Players

- `GET /api/players/<player_id>/behavior` — behavioural telemetry, anomalies, and event history.
- `POST /api/players/<player_id>/session` — log a fresh session payload.
- `GET /api/players/suspicious` — list high-risk players (threshold configurable).

### Analytics

- `GET /api/analytics/cheat-patterns` — frequency distribution of detected cheat signatures.
- `POST /api/analytics/detect-anomalies` — run anomaly detection for a player’s latest sessions.
- `GET /api/analytics/stats` — global telemetry metrics and the latest sessions.

Example request:

```bash
curl http://127.0.0.1:5000/api/security/player-risk/1 \
  -H "Authorization: Bearer <TOKEN>"
```

## Security & Compliance

- JWT authentication via `Authorization: Bearer` headers.
- In-memory rate limiting keyed by IP + endpoint with configurable thresholds.
- Request payload validation and bounded fields to deter injection vectors.
- SQLAlchemy ORM with parameterised queries (no raw SQL).
- CORS policy configurable via `CORS_ORIGINS`.

## Testing

```bash
pytest
```

Fixtures spin up an in-memory SQLite database with targeted telemetry so tests run quickly and deterministically.

## Docker Deployment

Build and run using Docker Compose:

```bash
cd docker
docker compose up --build
```

The service becomes available at `http://localhost:5000`. Persistence is backed by a volume-mounted `instance/` directory for the SQLite file.

## Architecture Notes

- `app/services/` encapsulates detection logic for re-use across routes and background jobs.
- `app/utils/` contains cross-cutting helpers: configuration, auth, database bootstrapping, and rate limiting.
- Logging is structured and ready for aggregation pipelines like CloudWatch, Splunk, or ELK.
- Sample data simulates live telemetry with abnormal headshot rates, sub-100ms reaction times, and skill spikes.

---

Built as part of a personal project to demonstrate practical anti-cheat monitoring capabilities.

