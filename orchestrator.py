"""Taku orchestrator: runs the agent swarm in sequence over a shared context."""

from agents.base import Agent

# Import agent subclasses here as they are built, e.g.:
# from agents.vision import VisionAgent

# Agent instances run in this order, each building on the shared context.
AGENTS: list[Agent] = []


def run_swarm(initial_context: dict) -> tuple[dict, list[dict]]:
    context = dict(initial_context)
    logs = []

    for agent in AGENTS:
        try:
            result = agent.run(context)
            print(f"✅ {agent.name} — OK")
            context = result
            logs.append(agent.log(f"done. context keys: {sorted(context.keys())}"))
        except Exception as e:
            print(f"❌ {agent.name} — FAILED: {e}")
            break

    return context, logs


if __name__ == "__main__":
    initial_context = {
        "image_url": "https://images.unsplash.com/photo-1593618998160-e34014e67546",
        "note": "Hand-forged Santoku, ~30000 yen",
    }

    final_context, logs = run_swarm(initial_context)

    print("\n=== Final context ===")
    print(final_context)
    print("\n=== Logs ===")
    for entry in logs:
        print(entry)
