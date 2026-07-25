import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = OpenAI(
    api_key=os.environ["QWEN_API_KEY"],
    base_url=os.environ["QWEN_BASE_URL"],
)

response = client.chat.completions.create(
    model=os.environ["QWEN_MODEL"],
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What object is this? Type, material, condition. Reply in JSON.",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://images.unsplash.com/photo-1593618998160-e34014e67546"
                    },
                },
            ],
        }
    ],
)

print("=== QWEN (qwen-vl-max) — Vision ===")
print(response.choices[0].message.content)
