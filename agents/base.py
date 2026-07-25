from datetime import datetime


class Agent:
    """Base class for every agent in the swarm.

    Subclasses set `name` and override `run()` to do their work.
    Each agent receives the shared context dict, updates it in place,
    and returns it so the next agent can build on it.
    """

    name = "Agent"

    def run(self, context: dict) -> dict:
        raise NotImplementedError("Subclasses must implement run()")

    def log(self, message: str) -> dict:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {self.name}: {message}")
        return {"time": timestamp, "agent": self.name, "message": message}
