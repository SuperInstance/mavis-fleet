"""Fleet CLI — captain's interface to the multi-substrate fleet."""
import argparse
import json
import sys
from pathlib import Path

from .core import fleet_health, fleet_canary, __version__, RSILoop
from .substrates import get_substrate, list_substrates, SUBSTRATE_CLASSES
from .agents import list_agents, AGENT_ROLES
from .bus import MessageBus
from .scheduler import Scheduler


def cmd_health(args):
    """Show fleet health."""
    h = fleet_health()
    if args.json:
        print(json.dumps(h, indent=1))
    else:
        print(f"=== mavis-fleet v{__version__} ===")
        print(f"Canary: {h['canary']}")
        print(f"All substrates available: {'✓' if h['all_available'] else '✗'}")
        print()
        for name, status in h["substrates"].items():
            mark = "✓" if status.get("available") else "✗"
            print(f"  {mark} {name:10s} {status}")


def cmd_run(args):
    """Run an experiment on a substrate."""
    substrate_name = args.substrate
    substrate = get_substrate(substrate_name)
    exp = {"type": args.type, "id": args.id}
    # Pass extra args as kwargs
    if args.arg:
        for a in args.arg:
            if "=" in a:
                k, v = a.split("=", 1)
                exp[k] = v
            else:
                exp[a] = True

    result = substrate.run(exp)
    print(f"Substrate: {result.substrate}")
    print(f"Experiment: {result.experiment_id}")
    print(f"Status: {result.status}")
    print(f"Metric: {result.metric}")
    print(f"Witness: {result.witness}")
    if args.json:
        print()
        print(json.dumps({
            "substrate": result.substrate,
            "experiment_id": result.experiment_id,
            "status": result.status,
            "metric": result.metric,
            "witness": result.witness,
            "output": result.output,
        }, indent=1, default=str))
    if not args.json:
        print(f"Output: {json.dumps(result.output, default=str)[:300]}")


def cmd_agents(args):
    """List available agents."""
    print(f"=== {len(list_agents())} agents ===")
    for role in list_agents():
        desc = AGENT_ROLES.get(role, "?")
        print(f"  {role}: {desc}")


def cmd_rsi(args):
    """Run an RSI iteration."""
    loop = RSILoop()
    iterations = args.iterations or 1
    records = loop.run(iterations=iterations)
    if args.json:
        print(json.dumps(records, indent=1))
    else:
        kept = sum(1 for r in records if r.get("scored", {}).get("kept"))
        print(f"=== RSI Loop ===")
        print(f"Iterations: {iterations}")
        print(f"Kept: {kept}/{iterations}")
        for i, r in enumerate(records):
            p = r["proposal"]
            print(f"\n  [{i+1}] {p.get('type')}: {p.get('rationale')[:80]}")
            if r.get("scored", {}).get("kept"):
                print(f"      KEPT (improvement: {r['scored']['improvement']:.3f})")


def cmd_publish(args):
    """Publish a message to the bus."""
    bus = MessageBus()
    msg_id = bus.publish(args.topic, {"text": args.text, "from": "cli"},
                          publisher=args.publisher)
    print(f"✓ Published: {msg_id}")


def cmd_subscribe(args):
    """Subscribe to messages on a topic."""
    bus = MessageBus()
    msgs = bus.subscribe(topic=args.topic, limit=args.limit)
    print(f"=== {len(msgs)} messages ===")
    for m in msgs:
        print(f"  [{m.get('timestamp', '?')[:19]}] {m.get('topic')} by {m.get('publisher')}: {str(m.get('payload'))[:80]}")


def cmd_schedule(args):
    """Add a task to the scheduler."""
    sched = Scheduler()
    task_id = sched.add(args.substrate, args.goal, priority=args.priority)
    print(f"✓ Added: {task_id}")
    print(f"  Substrate: {args.substrate}")
    print(f"  Goal: {args.goal}")
    print(f"  Priority: {args.priority}")


def cmd_pending(args):
    """Show pending tasks."""
    sched = Scheduler()
    pending = sched.pending()
    print(f"=== {len(pending)} pending tasks ===")
    for t in pending:
        print(f"  [{t['priority']}] {t['id']}: {t['goal'][:80]}")


def cmd_version(args):
    """Show version and canary."""
    print(f"mavis-fleet v{__version__}")
    print(f"Canary: {fleet_canary()}")


def main():
    p = argparse.ArgumentParser(description="mavis-fleet — multi-substrate RSI organizational system")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_h = sub.add_parser("health", help="Show fleet health")
    p_h.add_argument("--json", action="store_true")
    p_h.set_defaults(func=cmd_health)

    p_r = sub.add_parser("run", help="Run an experiment on a substrate")
    p_r.add_argument("substrate", choices=list_substrates())
    p_r.add_argument("--type", default="default")
    p_r.add_argument("--id")
    p_r.add_argument("--arg", action="append", help="key=value pairs")
    p_r.add_argument("--json", action="store_true")
    p_r.set_defaults(func=cmd_run)

    sub.add_parser("agents", help="List agents").set_defaults(func=cmd_agents)

    p_rsi = sub.add_parser("rsi", help="Run RSI iterations")
    p_rsi.add_argument("--iterations", type=int, default=1)
    p_rsi.add_argument("--json", action="store_true")
    p_rsi.set_defaults(func=cmd_rsi)

    p_pub = sub.add_parser("publish", help="Publish to bus")
    p_pub.add_argument("topic")
    p_pub.add_argument("text")
    p_pub.add_argument("--publisher", default="cli")
    p_pub.set_defaults(func=cmd_publish)

    p_sub = sub.add_parser("subscribe", help="Subscribe to bus")
    p_sub.add_argument("--topic", help="Filter by topic")
    p_sub.add_argument("--limit", type=int, default=10)
    p_sub.set_defaults(func=cmd_subscribe)

    p_sch = sub.add_parser("schedule", help="Add a task")
    p_sch.add_argument("substrate")
    p_sch.add_argument("goal")
    p_sch.add_argument("--priority", type=int, default=5)
    p_sch.set_defaults(func=cmd_schedule)

    sub.add_parser("pending", help="Show pending tasks").set_defaults(func=cmd_pending)
    sub.add_parser("version", help="Show version").set_defaults(func=cmd_version)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
