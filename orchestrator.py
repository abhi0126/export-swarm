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
from agents.export_intelligence import ExportIntelligenceAgent
from agents.verification import VerificationAgent

# Agent instances run in this order, each building on the shared context.
AGENTS: list[Agent] = [
    IntakeAgent(),
    MerchandisingAgent(),
    VerificationAgent(),
    ExportIntelligenceAgent(),
]


MAX_ATTEMPTS = 3


def run_swarm(initial_context: dict, on_event=None) -> tuple[dict, list[dict]]:
    """Run agents in sequence. on_event(status, agent_name, context) is called
    with status "running" / "done" / "failed" around each agent (web layer hook)."""
    context = dict(initial_context)
    logs = []

    for agent in AGENTS:
        if on_event:
            on_event("running", agent.name, context)
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                result = agent.run(context)
                print(f"✅ {agent.name} — OK")
                context.update(result)
                logs.append(agent.log(f"done. context keys: {sorted(context.keys())}"))
                if on_event:
                    on_event("done", agent.name, context)
                break
            except Exception as e:
                if attempt < MAX_ATTEMPTS:
                    print(f"⚠️ {agent.name} — retry {attempt}/{MAX_ATTEMPTS}: {e}")
                    time.sleep(attempt)  # backoff: 1s, then 2s
                else:
                    print(f"❌ {agent.name} — FAILED: {e}")
                    last_error = e
        else:
            if on_event:
                on_event("failed", agent.name, context)
            # Agent exhausted its retries — stop the swarm and propagate so
            # callers (e.g. the web layer) can surface the real error.
            raise last_error

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
            "手打ちの三徳包丁、約30,000円。岐阜県関市で製作。"
            "VG-10ステンレスの芯にダマスカス積層。"
            "工房は1954年創業、三代目の刀鍛冶。"
        ),
    }

    final_context, logs = run_swarm(initial_context)

    print("\n=== Final context ===")
    print(final_context)
    print("\n=== Logs ===")
    for entry in logs:
        print(entry)
