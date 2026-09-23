"""Scheduler — priority queue for fleet tasks."""
import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional

from .core import SUBSTRATES


class Scheduler:
    """Priority queue for tasks.

    Tasks have:
    - priority: 1 (captain's orders) - 5 (study/idle)
    - substrate: which substrate to run on
    - goal: what to do
    - dependencies: list of task IDs that must finish first
    """

    PRIORITIES = {
        1: "captain's orders",
        2: "triggered work",
        3: "follow-up work",
        4: "maintenance",
        5: "study",
    }

    def __init__(self):
        self.tasks: Dict[str, Dict] = {}

    def add(self, substrate: str, goal: str, priority: int = 5,
            dependencies: Optional[List[str]] = None) -> str:
        """Add a task to the queue."""
        if substrate not in SUBSTRATES:
            raise ValueError(f"unknown substrate: {substrate}")
        if priority not in self.PRIORITIES:
            raise ValueError(f"invalid priority: {priority}")

        task_id = f"task-{len(self.tasks) + 1}-{int(datetime.datetime.utcnow().timestamp())}"
        self.tasks[task_id] = {
            "id": task_id,
            "substrate": substrate,
            "goal": goal,
            "priority": priority,
            "status": "pending",
            "dependencies": dependencies or [],
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        }
        return task_id

    def ready(self) -> List[str]:
        """Get ready-to-run tasks (no unmet dependencies)."""
        ready = []
        for tid, task in self.tasks.items():
            if task["status"] != "pending":
                continue
            deps = task["dependencies"]
            unmet = [
                d for d in deps
                if self.tasks.get(d, {}).get("status") != "success"
            ]
            if not unmet:
                ready.append(tid)
        # Sort by priority (1 first)
        ready.sort(key=lambda t: self.tasks[t]["priority"])
        return ready

    def pending(self) -> List[Dict]:
        """Get pending tasks (in priority order)."""
        result = [self.tasks[t] for t in self.ready()]
        return sorted(result, key=lambda t: t["priority"])

    def complete(self, task_id: str, success: bool = True):
        """Mark a task complete."""
        if task_id not in self.tasks:
            return False
        self.tasks[task_id]["status"] = "success" if success else "failed"
        self.tasks[task_id]["completed_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        return True

    def stats(self) -> Dict:
        """Get scheduler stats."""
        by_status = {"pending": 0, "success": 0, "failed": 0, "running": 0}
        for t in self.tasks.values():
            by_status[t["status"]] = by_status.get(t["status"], 0) + 1

        by_substrate = {}
        for t in self.tasks.values():
            s = t["substrate"]
            by_substrate[s] = by_substrate.get(s, 0) + 1

        return {
            "total": len(self.tasks),
            "by_status": by_status,
            "by_substrate": by_substrate,
        }
