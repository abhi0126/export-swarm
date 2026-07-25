"""Taku orchestrator: runs the agent swarm in sequence over a shared context."""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agents.base import Agent
from agents.intake import IntakeAgent
from agents.merchandising import MerchandisingAgent
from agents.verification import VerificationAgent

# Agent instances run in this order, each building on the shared context.
AGENTS: list[Agent] = [
    IntakeAgent(),
    MerchandisingAgent(),
    VerificationAgent(),
]


MAX_ATTEMPTS = 3


def run_swarm(initial_context: dict) -> tuple[dict, list[dict]]:
    context = dict(initial_context)
    logs = []

    for agent in AGENTS:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                result = agent.run(context)
                print(f"✅ {agent.name} — OK")
                context.update(result)
                logs.append(agent.log(f"done. context keys: {sorted(context.keys())}"))
                break
            except Exception as e:
                if attempt < MAX_ATTEMPTS:
                    print(f"⚠️ {agent.name} — retry {attempt}/{MAX_ATTEMPTS}: {e}")
                    time.sleep(attempt)  # backoff: 1s, then 2s
                else:
                    print(f"❌ {agent.name} — FAILED: {e}")
        else:
            break  # agent exhausted its retries — stop the swarm

    return context, logs


def warmup() -> None:
    """Fire one trivial call per provider to wake cold endpoints before a demo."""
    load_dotenv(Path(__file__).resolve().parent / ".env")

    providers = [("Qwen", "QWEN"), ("GMI", "GMI"), ("ai&", "AI_AND")]

    for name, prefix in providers:
        try:
            client = OpenAI(
                api_key=os.environ[f"{prefix}_API_KEY"],
                base_url=os.environ[f"{prefix}_BASE_URL"],
            )
            client.chat.completions.create(
                model=os.environ[f"{prefix}_MODEL"],
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5,
            )
            print(f"🔥 {name} — warm")
        except Exception as e:
            print(f"❌ {name} — warmup FAILED: {e}")


if __name__ == "__main__":
    if "--warmup" in sys.argv:
        warmup()
        sys.exit(0)

    initial_context = {
        "image_url": "https://images.unsplash.com/photo-1593618998160-e34014e67546",
        "note": (
            "Hand-forged Santoku, ~30000 yen. Made in Seki, Gifu Prefecture. "
            "VG-10 stainless core with damascus cladding. "
            "Workshop founded 1954, third-generation smith."
        ),
    }

    final_context, logs = run_swarm(initial_context)

    print("\n=== Final context ===")
    print(final_context)
    print("\n=== Logs ===")
    for entry in logs:
        print(entry)
