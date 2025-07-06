from slack_bolt import App as SlackApp
from slack_bolt.adapter.fastapi import SlackRequestHandler
from fastapi import FastAPI, Request
import os
from dotenv import load_dotenv

from langgraph_flow import app as langgraph_app  # LangGraph flow
from app.db import init_db, save_report_to_db
from app.utils.chart_generator import generate_contribution_chart
from app.utils.slack_utils import upload_chart_to_slack

# Load env and init DB
load_dotenv()
init_db()

# Environment validation
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

if not SLACK_BOT_TOKEN or not SLACK_SIGNING_SECRET:
    raise ValueError("❌ SLACK_BOT_TOKEN or SLACK_SIGNING_SECRET not set in .env")

# Initialize Slack App
slack_app = SlackApp(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)

# Slash Command Handler
@slack_app.command("/dev-report")
def handle_dev_report(ack, say, command):
    ack()
    say("📊 Generating your weekly dev report...")

    try:
        # 1. Run LangGraph pipeline
        result = langgraph_app.invoke({})

        # 2. Send summary
        summary = result.get("summary", "No summary available.")
        say(summary)

        # 3. Save to DB
        save_report_to_db(result)
        print("✅ Report saved to DB.")

        # 4. Upload chart if per-author stats exist
        per_author = result.get("per_author_diff", {})  # FIX: consistent key
        if isinstance(per_author, dict) and any(per_author.values()):
            chart_path = generate_contribution_chart(per_author)
            if chart_path:
                upload_chart_to_slack(command["channel_id"], chart_path)
            else:
                say("_Chart generation failed._")
        else:
            say("_No contribution data available to plot._")

    except Exception as e:
        print("❌ Error:", e)
        say("❌ An internal error occurred while processing the report.")

# FastAPI app + Slack Events adapter
fastapi_app = FastAPI()
handler = SlackRequestHandler(slack_app)

@fastapi_app.post("/slack/events")
async def slack_events(request: Request):
    return await handler.handle(request)
