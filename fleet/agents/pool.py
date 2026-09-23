"""Concrete agent implementations."""

from .base import Agent


class ResearcherAgent(Agent):
    role = "researcher"
    description = "Investigates substrates via experiments"

    def run(self, task):
        substrate = task.get("substrate", "quilt")
        return {"substrate": substrate, "experiment": task.get("experiment"), "ok": True}


class TeacherAgent(Agent):
    role = "teacher"
    description = "Explains canon and doctrines"

    def run(self, task):
        return {"topic": task.get("topic"), "explained": True}


class CriticAgent(Agent):
    role = "critic"
    description = "Reviews outputs for canon alignment"

    def run(self, task):
        target = task.get("target", "")
        return {
            "target": target,
            "scores": {
                "doctrine_alignment": 0.85,
                "polyformality": 0.70,
                "clarity": 0.80,
            },
            "issues": [],
        }


class DistillerAgent(Agent):
    role = "distiller"
    description = "Compresses patterns into doctrines"

    def run(self, task):
        return {"new_doctrine": task.get("pattern", "unnamed")}


class EditorAgent(Agent):
    role = "editor"
    description = "Rewrites canon while preserving doctrine"

    def run(self, task):
        return {"rewritten": True, "input": task.get("text", "")}


class WriterAgent(Agent):
    role = "writer"
    description = "Generates new canon pieces"

    def run(self, task):
        return {"piece_id": task.get("id", "new")}


class CodeReviewerAgent(Agent):
    role = "code_reviewer"
    description = "Reviews code against bedrock principles"

    def run(self, task):
        return {"file": task.get("file"), "reviewed": True}


class ConsistencyAgent(Agent):
    role = "consistency"
    description = "Cross-substrate consistency checker"

    def run(self, task):
        return {"consistent": True, "substrates_checked": ["quilt", "moth", "jev"]}


class CoordinatorAgent(Agent):
    role = "coordinator"
    description = "Routes tasks to the right substrate"

    def run(self, task):
        return {"routed_to": task.get("substrate", "quilt")}


class ProjectManagerAgent(Agent):
    role = "project_manager"
    description = "Tracks deliverables, knows status"

    def run(self, task):
        return {"status": task.get("status", "in_progress")}


class ScientistAgent(Agent):
    role = "scientist"
    description = "Designs and runs experiments"

    def run(self, task):
        return {"experiment": task.get("id"), "ran": True}


class StrategyAgent(Agent):
    role = "strategy"
    description = "Sets fleet priorities"

    def run(self, task):
        return {"priorities": task.get("priorities", [])}


class SecurityAgent(Agent):
    role = "security"
    description = "Audits substrate access"

    def run(self, task):
        return {"audited": task.get("scope", "all"), "issues": []}


class PoolAgent(Agent):
    role = "pool"
    description = "Provides elastic capacity"

    def run(self, task):
        return {"scaled": True, "added_agents": task.get("count", 1)}


AGENT_CLASSES = {
    "researcher": ResearcherAgent,
    "teacher": TeacherAgent,
    "critic": CriticAgent,
    "distiller": DistillerAgent,
    "editor": EditorAgent,
    "writer": WriterAgent,
    "code_reviewer": CodeReviewerAgent,
    "consistency": ConsistencyAgent,
    "coordinator": CoordinatorAgent,
    "project_manager": ProjectManagerAgent,
    "scientist": ScientistAgent,
    "strategy": StrategyAgent,
    "security": SecurityAgent,
    "pool": PoolAgent,
}


def get_agent(role: str) -> Agent:
    cls = AGENT_CLASSES.get(role)
    if not cls:
        raise ValueError(f"unknown agent role: {role}")
    return cls()


def list_agents() -> list:
    return list(AGENT_CLASSES.keys())
