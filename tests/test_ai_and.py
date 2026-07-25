import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = OpenAI(
    api_key=os.environ["AI_AND_API_KEY"],
    base_url=os.environ["AI_AND_BASE_URL"],
)

response = client.chat.completions.create(
    model=os.environ["AI_AND_MODEL"],
    messages=[
        {
            "role": "user",
            "content": "Translate to English: この包丁は職人が一つ一つ手作りしています。",
        }
    ],
)

print("=== AI_AND (deepseek-v4-pro) — Text ===")
print(response.choices[0].message.content)
