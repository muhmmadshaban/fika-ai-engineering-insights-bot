# 🧠 FIKA AI Engineering Insights Bot

A modular engineering insights bot that tracks GitHub activity, analyzes PR/commit patterns, identifies churn outliers, and generates DORA-aligned weekly summaries — with optional Slack integration.

## 📁 Project Structure

```
fika-ai-engineering-insights-bot/
│
├── app/
│   ├── agents/
│   │   ├── data_harvester.py       # GitHub events harvester
│   │   ├── diff_analyst.py         # Churn and per-author analyzer
│   │   ├── insight_narrator.py     # Summarizer (DORA + narrative)
│   ├── slack_bot.py                # Slack event handler (optional)
│   ├── db.py                       # SQLite interaction
│
├── data/
│   └── fake_github_events.json     # Sample GitHub event payloads
│
├── scripts/
│   └── seed_db.py                  # Seeds DB using fake events
│
├── docker-compose.yml             # One-command bootstrap
├── requirements.txt               # Python dependencies
├── .env                           # Environment variables
├── weekly_reports.db              # SQLite DB file
├── audit_log.jsonl                # Logs of all summaries
├── README.md                      # You're reading it!
```

---

## 🚀 Features

- ✅ GitHub PR and commit ingestion via REST or webhook
- ✅ Churn analysis with outlier detection
- ✅ Per-author diff stats (lines added, deleted, files changed)
- ✅ Weekly dev summaries mapped to **DORA metrics**
- ✅ Slack summary output (optional)
- ✅ SQLite DB storage
- ✅ Fake seed data for instant demos
- ✅ One-command bootstrap (`docker-compose up`)

---

## 📦 Requirements

- Python 3.8+
- Docker (optional but recommended for one-command run)

Install dependencies locally:

```bash
pip install -r requirements.txt
```

---

## 🛠️ Usage

### ➤ 1. Seed the Database (with fake data)

```bash
python scripts/seed_db.py
```

This script will load `data/fake_github_events.json`, run all agents, and populate `weekly_reports.db`.

### ➤ 2. Run the App

#### Option 1: 🐳 Docker Compose (recommended)

```bash
docker-compose up
```

#### Option 2: Local FastAPI Server

```bash
uvicorn slack_bot:fastapi_app --reload --port 3000
```

### ➤ 3. Slack Integration (Optional)

Create a Slack app and expose your server (e.g., with `ngrok`) to receive `/slack/events` via `POST`. Update `.env` with:

```
SLACK_BOT_TOKEN=xoxb-***
SLACK_SIGNING_SECRET=***
```



---

## 📊 Example Output

```
📊 This week in development:
- Review latency averaged 2.58 hours.
- Cycle time held steady at 5.48 hours.
- 69.5% of PRs were merged.
- There were 0 CI failures.
- Top contributor: *hediet* with +6409 / -795 on 86 file(s).
⚠️ High churn activity detected from: hediet, lszomoru, roblourens.
```

---

## 📌 TODO

- [ ] Add GitHub REST polling or webhook support
- [ ] Enhance LLM summaries with change context
- [ ] Add dashboard for visualizing trends
- [ ] CI/CD via GitHub Actions

---

## 📜 License

MIT License. Open source and free to use 🚀

---

## 👨‍💻 Author

Made with ❤️ by Muhmmad Shaban