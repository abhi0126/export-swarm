import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agents.base import Agent

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PROMPT = """You are the merchandising lead for a Japanese craftsman's export shop.

Product analysis (from vision intake):
{product_analysis}

Craftsman's note (written in Japanese — extract the facts regardless of language): {note}

Return ONLY JSON (no prose, no markdown fences) with keys:
- "listing_en": a compelling English product listing (2-3 sentences)
- "story": provenance and heritage (3-4 sentences). STRICT GROUNDING RULES:
  Use ONLY the region, materials, and workshop details supplied above in the
  note and product analysis. Do NOT invent a region, a workshop history, a
  technique name, or any specific tradition not present in the input. If a
  detail isn't supplied, write around it rather than inventing it. You MAY
  explain general cultural context (e.g. what Santoku means, the role of
  knives in washoku) since that is genuine background, not fabricated
  provenance.
- "translations": an object with "ja", "fr", "de" keys, each a one-paragraph
  version of the listing in that language"""


class MerchandisingAgent(Agent):
    name = "Merchandising"

    def run(self, context: dict) -> dict:
        self.log("Writing listing and provenance story")

        client = OpenAI(
            api_key=os.environ["GMI_API_KEY"],
            base_url=os.environ["GMI_BASE_URL"],
            timeout=150,  # GMI legitimately takes ~80s on this call
        )

        response = client.chat.completions.create(
            model=os.environ["GMI_MODEL"],
            messages=[
                {
                    "role": "user",
                    "content": PROMPT.format(
                        product_analysis=json.dumps(context["product_analysis"], indent=2),
                        note=context["note"],
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

        first_line = data["listing_en"].splitlines()[0]
        self.log(f"Listing: {first_line}")
        return {"merchandising": data}
