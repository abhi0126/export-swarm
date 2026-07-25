import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = OpenAI(
    api_key=os.environ["GMI_API_KEY"],
    base_url=os.environ["GMI_BASE_URL"],
)

response = client.chat.completions.create(
    model=os.environ["GMI_MODEL"],
    messages=[
        {
            "role": "user",
            "content": "Write a 2-sentence product listing for a hand-forged Japanese kitchen knife.",
        }
    ],
)

print("=== GMI (DeepSeek-V3.2) — Text ===")
print(response.choices[0].message.content)
