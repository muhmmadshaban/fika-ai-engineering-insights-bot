from slack_sdk import WebClient
import os

client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

def upload_chart_to_slack(channel_id, chart_path):
    try:
        response = client.files_upload_v2(
            channels=[channel_id],
            file=chart_path,
            title="Developer Contribution Chart",
            filename="dev_report_chart.png",
            initial_comment="📊 *Weekly Dev Chart*"
        )
        print("✅ Chart uploaded successfully.")
    except Exception as e:
        print("❌ Failed to upload chart:", e)
