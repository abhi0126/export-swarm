import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agents.base import Agent

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class IntakeAgent(Agent):
    name = "Intake"

    def run(self, context: dict) -> dict:
        self.log("Reading product photos with Qwen-VL")

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
                            "text": (
                                "Analyze this craft product. Return ONLY JSON with keys: "
                                "type, material, condition, notable_features. "
                                "No prose, no markdown fences."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": context["image_url"]},
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
