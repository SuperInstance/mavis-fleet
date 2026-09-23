"""Base agent interface and role definitions."""
import abc
from typing import Dict, List, Optional


class Agent(abc.ABC):
    """Abstract base for all fleet agents."""

    role: str = "agent"
    description: str = ""

    @abc.abstractmethod
    def run(self, task: Dict) -> Dict:
        """Process a task and return a result."""
        ...

    def description_lines(self) -> List[str]:
        """Standard description for CLI display."""
        return [
            f"role: {self.role}",
            f"description: {self.description}",
        ]


AGENT_ROLES = {
    "researcher": "Investigates substrates, surfaces insights, gathers evidence",
    "teacher": "Explains canon and doctrines to other agents or humans",
    "critic": "Reviews outputs for canon alignment, doctrine adherence",
    "distiller": "Compresses repeated patterns into named doctrines",
    "editor": "Rewrites canon for clarity while preserving doctrine",
    "writer": "Generates new canon pieces via chord-validated pulses",
    "code_reviewer": "Reviews code changes against bedrock principles",
    "consistency": "Checks for canonical consistency across substrates",
    "coordinator": "Routes tasks to the right substrates and agents",
    "project_manager": "Tracks deliverables, knows what's done vs pending",
    "scientist": "Runs RSI loops, designs experiments, evaluates",
    "strategy": "Decides fleet priorities based on canon momentum",
    "security": "Validates gateways, audits substrate access",
    "pool": "Provides elastic agent capacity when one role is overloaded",
}
