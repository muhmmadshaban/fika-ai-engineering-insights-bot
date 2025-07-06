from dotenv import load_dotenv
load_dotenv()

from together import Together

client = Together()  # uses TOGETHER_API_KEY from .env

def generate_summary_via_llm(metrics):
    prompt = f"""Summarize this GitHub engineering activity:
{metrics}

Focus on DORA metrics and team insight. Use **hours** for latency and cycle time (not days). Keep the summary concise, under 100 words."""
    
    response = client.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.1",  # You can also try other Together-supported models
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
