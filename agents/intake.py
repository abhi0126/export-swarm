import base64
import json
import mimetypes
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agents.base import Agent

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _to_image_url(image_url: str) -> str:
    """Remote URLs pass through unchanged. Local files (e.g. /static/uploads/...)
    are base64-encoded into a data URL — Qwen can't fetch localhost paths over
    the internet, so we send the image bytes inline instead."""
    if image_url.startswith(("http://", "https://")):
        return image_url
    path = Path(__file__).resolve().parent.parent / image_url.lstrip("/")
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


class IntakeAgent(Agent):
    name = "Intake"

    def run(self, context: dict) -> dict:
        self.log("Reading product photos with Qwen-VL")

        client = OpenAI(
            api_key=os.environ["QWEN_API_KEY"],
            base_url=os.environ["QWEN_BASE_URL"],
            timeout=60,  # fail fast into the retry path on stalled requests
        )

        response = client.chat.completions.create(
            model=os.environ["QWEN_MODEL"],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this craft product. Return ONLY JSON with keys: "
                                "type, material, condition, notable_features. "
                                "No prose, no markdown fences. "
                                "Do NOT include brand names, logos, or maker marks "
                                "anywhere in the output — describe only physical "
                                "characteristics: shape, materials, construction, "
                                "finish, included items."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": _to_image_url(context["image_url"])},
                        },
                    ],
                }
            ],
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if the model adds them anyway
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print("Raw model response (JSON parse failed):")
            print(raw)
            raise

        self.log(f"Extracted: {data.get('type')}")
        return {"product_analysis": data}
