import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agents.base import Agent

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PROMPT = """You are a bilingual quality checker for a Japanese craftsman's export shop.

Original English listing:
{listing_en}

Japanese translation shown to buyers:
{ja}

Return ONLY JSON (no prose, no markdown fences) with keys:
- "back_translation": the Japanese text translated back into English
- "meaning_match": "ok" or "mismatch" — does the Japanese convey the same
  meaning as the original English listing?
- "tone_check": "ok" or "flagged" — is the politeness level and register
  appropriate for a product listing aimed at overseas buyers?
- "notes": brief explanation of any mismatch or tone issue, empty string if fine"""


class VerificationAgent(Agent):
    name = "Verification"

    def run(self, context: dict) -> dict:
        self.log("Back-translating Japanese output and checking tone")

        client = OpenAI(
            api_key=os.environ["AI_AND_API_KEY"],
            base_url=os.environ["AI_AND_BASE_URL"],
            timeout=60,  # fail fast into the retry path on stalled requests
        )

        response = client.chat.completions.create(
            model=os.environ["AI_AND_MODEL"],
            messages=[
                {
                    "role": "user",
                    "content": PROMPT.format(
                        listing_en=context["merchandising"]["listing_en"],
                        ja=context["merchandising"]["translations"]["ja"],
                    ),
                }
            ],
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print("Raw model response (JSON parse failed):")
            print(raw)
            raise

        self.log(f"meaning_match={data.get('meaning_match')}, tone_check={data.get('tone_check')}")
        return {"verification": data}
