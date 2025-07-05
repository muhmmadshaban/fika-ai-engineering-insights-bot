from slack_bolt import App as SlackApp
from slack_bolt.adapter.fastapi import SlackRequestHandler
from fastapi import FastAPI, Request
import os
from dotenv import load_dotenv

from langgraph_flow import app as langgraph_app  # LangGraph flow
from db import init_db, save_report_to_db
from utils.chart_generator import generate_contribution_chart
from utils.slack_utils import upload_chart_to_slack

# Load environment variables early
load_dotenv()
init_db()

# Initialize Slack app
slack_app = SlackApp(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)

# Slash command handler
@slack_app.command("/dev-report")
def handle_dev_report(ack, say, command):
    print("✅ Slash command received:", command)
    ack()

    try:
        # Step 1: Run LangGraph app (collect + analyze GitHub data)
        result = langgraph_app.invoke({})

        # Step 2: Send summary to Slack
        summary = result.get("summary", "No summary available.")
        say(summary)

        # Step 3: Store weekly report in DB
        save_report_to_db(result)
        print("✅ Report saved to DB.")
        print("📡 Channel ID:", command.get("channel_id"))

        # Step 4: Generate and upload chart (if data available)
        per_author = result.get("per_author_diff", {})
        if per_author and isinstance(per_author, dict) and any(per_author.values()):
            chart_path = generate_contribution_chart(per_author)

            if chart_path:
                upload_chart_to_slack(command["channel_id"], chart_path)
            else:
                say("_Chart generation failed._")
        else:
            say("_No contribution data available to plot._")

    except Exception as e:
        print("❌ Error:", str(e))
        say("❌ An internal error occurred while processing the report.")

# Create FastAPI app and Slack event route
fastapi_app = FastAPI()
handler = SlackRequestHandler(slack_app)

@fastapi_app.post("/slack/events")
async def slack_events(request: Request):
    return await handler.handle(request)
