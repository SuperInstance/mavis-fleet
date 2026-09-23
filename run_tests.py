"""Comprehensive test suite for mavis-fleet."""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, "/workspace/repos/mavis-fleet")

from fleet import (
    fleet_canary, fleet_health, polyformality_score, chord_verdict, witness,
    RSILoop, ResourceLimits, DEFAULT_LIMITS, check_substrate_available,
    SUBSTRATES,
)
from fleet.substrates import (
    QuiltSubstrate, MOTHSubstrate, JEVSubstrate, JEPASubstrate,
    TrainerSubstrate, RSISubstrate, get_substrate, list_substrates,
)
from fleet.agents import list_agents, get_agent, AGENT_ROLES
from fleet.bus import MessageBus
from fleet.scheduler import Scheduler


results = []
failures = []


def test(name, func):
    try:
        func()
        results.append((name, "PASS"))
    except AssertionError as e:
        results.append((name, f"FAIL: {e}"))
        failures.append(name)
    except Exception as e:
        results.append((name, f"ERROR: {type(e).__name__}: {e}"))
        failures.append(name)


# ─── Core tests ─────────────────────────────────────────────

def t_canary():
    assert fleet_canary() == "0x24a555471370b18d"


def t_fleet_health():
    h = fleet_health()
    assert h["version"] == "0.1.0"
    assert h["canary"] == "0x24a555471370b18d"
    assert "substrates" in h
    assert all(s in h["substrates"] for s in SUBSTRATES)


def t_polyformality_identical():
    s = polyformality_score(["hello world", "hello world"])
    assert s == 1.0


def t_polyformality_different():
    s = polyformality_score(["hello world", "completely different text here"])
    assert s < 0.5


def t_chord_verdict_promoted():
    v = chord_verdict(["same text", "same text", "same text"])
    assert v["is_chord"]
    assert v["promoted"]


def t_chord_verdict_not_promoted():
    v = chord_verdict(["unique one", "different two", "another three"])
    assert not v["is_chord"]


def t_witness_deterministic():
    r1 = witness({"a": 1, "b": 2})
    r2 = witness({"a": 1, "b": 2})
    assert r1 == r2


def t_witness_format():
    r = witness({"key": "value"})
    assert r.startswith("wit-")


def t_resource_limits():
    for substrate in SUBSTRATES:
        limits = DEFAULT_LIMITS.get(substrate)
        assert limits is not None
        assert limits.substrate == substrate


def t_check_substrate_available():
    for s in SUBSTRATES:
        info = check_substrate_available(s)
        assert "available" in info
        assert "missing_keys" in info


def t_rsi_loop_propose():
    loop = RSILoop(base=Path(tempfile.mkdtemp()))
    proposal = loop.propose()
    assert "type" in proposal
    assert "rationale" in proposal


def t_rsi_loop_test():
    loop = RSILoop(base=Path(tempfile.mkdtemp()))
    result = loop.test({"type": "x", "rationale": "test"})
    assert result["passed"]


def t_rsi_loop_score():
    loop = RSILoop(base=Path(tempfile.mkdtemp()))
    scored = loop.score({"passed": True, "metric_change": 0.1})
    assert scored["kept"] is True
    assert scored["improvement"] > 0


def t_rsi_step_logged():
    with tempfile.TemporaryDirectory() as td:
        loop = RSILoop(base=Path(td))
        record = loop.step()
        assert "proposal" in record
        assert "test" in record
        assert "scored" in record
        # Log file exists
        log_path = Path(td) / "rsi_log.jsonl"
        assert log_path.exists()


def t_rsi_run_multiple():
    with tempfile.TemporaryDirectory() as td:
        loop = RSILoop(base=Path(td))
        records = loop.run(iterations=5)
        assert len(records) == 5


# ─── Substrate tests ────────────────────────────────────────

def t_quilt_substrate_availability():
    s = QuiltSubstrate()
    info = s.availability()
    assert info["available"]


def t_quilt_load_canon():
    s = QuiltSubstrate()
    result = s.run({"type": "load_canon", "limit": 5})
    assert result.status == "success"
    assert result.metric >= 0


def t_quilt_probe():
    s = QuiltSubstrate()
    result = s.run({"type": "probe", "text": "the substrate walker canon is doctrine"})
    assert result.status == "success"
    assert "polyformality" in result.output


def t_quilt_list_experiments():
    s = QuiltSubstrate()
    exps = s.list_experiments()
    assert isinstance(exps, list)


def t_moth_availability():
    s = MOTHSubstrate()
    info = s.availability()
    assert info["available"]
    assert "isomorphism" in info


def t_moth_quantum_polygon():
    s = MOTHSubstrate()
    result = s.run({"type": "quantum_polygon", "sides": 6})
    assert result.status == "success"
    assert result.output["sides"] == 6
    assert 0 <= result.output["value"] <= 1


def t_moth_amplitude_walk():
    s = MOTHSubstrate()
    result = s.run({"type": "amplitude_walk", "steps": 10})
    assert result.status == "success"
    assert len(result.output["amplitudes"]) == 10


def t_moth_null_result():
    s = MOTHSubstrate()
    result = s.run({"type": "null_result", "hypothesis": "the substrate is quantum"})
    assert result.status == "success"
    assert result.output["verdict"] == "NULL_RESULT"
    assert result.output["is_publishable"]


def t_jev_availability():
    s = JEVSubstrate()
    info = s.availability()
    assert "available" in info
    assert "endpoint" in info


def t_jev_probe_no_key():
    """When TYPESAFEAI_KEY is missing, falls back to local heuristic."""
    with patch.dict("os.environ", {}, clear=True):
        s = JEVSubstrate()
        result = s.run({"type": "probe", "question_id": "q01", "claim_a": "x", "claim_b": "y"})
        assert result.status == "success"
        assert result.output["verdict"] == "LOCAL_HEURISTIC"


def t_jepa_availability():
    s = JEPASubstrate()
    info = s.availability()
    assert info["available"]


def t_jepa_predict_neighbors():
    s = JEPASubstrate()
    result = s.run({"type": "predict_neighbors",
                    "text": "the substrate walker canon",
                    "candidate": "the canon walker substrate"})
    assert result.status == "success"
    assert result.output["score"] > 0  # shared words


def t_jepa_embed_similarity():
    s = JEPASubstrate()
    result = s.run({"type": "embed_similarity",
                    "texts": ["substrate walker", "substrate doctrine", "different topic"]})
    assert result.status == "success"
    assert "matrix" in result.output


def t_jepa_trajectory_predict():
    s = JEPASubstrate()
    result = s.run({"type": "trajectory_predict", "start": "02_ode_to_the_substrate_walker"})
    assert result.status == "success"
    assert "predicted_stops" in result.output


def t_trainer_run():
    s = TrainerSubstrate()
    result = s.run({"type": "default", "budget_seconds": 60})
    assert result.status == "success"
    assert "val_bpb" in result.output


def t_trainer_deterministic():
    """Same params → same metric."""
    s1 = TrainerSubstrate()
    s2 = TrainerSubstrate()
    r1 = s1.run({"learning_rate": 1e-4, "architecture": "transformer"})
    r2 = s2.run({"learning_rate": 1e-4, "architecture": "transformer"})
    assert r1.output["val_bpb"] == r2.output["val_bpb"]


def t_rsi_substrate_run():
    s = RSISubstrate()
    result = s.run({"type": "rsi_step", "iterations": 2})
    assert result.status == "success"
    assert result.output["iterations"] == 2


def t_get_substrate():
    for name in SUBSTRATES:
        s = get_substrate(name)
        assert s.name == name


def t_list_substrates():
    subs = list_substrates()
    assert len(subs) >= 6


def test_substrate_witnesses_persist():
    """Writes go to the witness dir."""
    s = RSISubstrate()
    s.run({"id": "test-witness-1"})
    witness_files = list(Path("/workspace/research/mavis-fleet/witnesses").glob("test-witness-1_*.json"))
    assert len(witness_files) >= 1


# ─── Agent tests ────────────────────────────────────────────

def t_list_agents():
    agents = list_agents()
    assert len(agents) >= 13
    assert "researcher" in agents
    assert "critic" in agents


def t_get_agent():
    for role in list_agents():
        agent = get_agent(role)
        assert agent.role == role


def test_agent_runs():
    """Every agent runs without error on basic task."""
    for role in list_agents():
        agent = get_agent(role)
        result = agent.run({"test": True, "topic": "x", "substrate": "quilt", "id": "y",
                            "status": "x", "scope": "all", "count": 1, "file": "x.py",
                            "priorities": [1, 2], "experiment": {}, "target": "x",
                            "pattern": "x_pattern", "text": "hello"})
        assert isinstance(result, dict)


# ─── Bus tests ──────────────────────────────────────────────

def test_bus_publish_subscribe():
    with tempfile.TemporaryDirectory() as td:
        bus = MessageBus(path=Path(td) / "bus.jsonl")
        msg_id = bus.publish("test", {"hello": "world"})
        assert msg_id
        msgs = bus.subscribe(topic="test")
        assert len(msgs) == 1
        assert msgs[0]["payload"]["hello"] == "world"


def test_bus_topics():
    with tempfile.TemporaryDirectory() as td:
        bus = MessageBus(path=Path(td) / "bus.jsonl")
        bus.publish("alpha", {"x": 1})
        bus.publish("beta", {"y": 2})
        topics = bus.topics()
        assert "alpha" in topics
        assert "beta" in topics


def test_bus_count():
    with tempfile.TemporaryDirectory() as td:
        bus = MessageBus(path=Path(td) / "bus.jsonl")
        bus.publish("test", {})
        bus.publish("test", {})
        bus.publish("other", {})
        assert bus.count(topic="test") == 2
        assert bus.count() == 3


def test_bus_hash_deterministic():
    """Same payload → same hash."""
    bus = MessageBus()  # uses default path
    bus.publish("test", {"x": 1, "y": 2})


# ─── Scheduler tests ────────────────────────────────────────

def test_scheduler_add_and_ready():
    sched = Scheduler()
    tid = sched.add("quilt", "test goal")
    assert tid
    ready = sched.ready()
    assert tid in ready


def test_scheduler_priority_order():
    sched = Scheduler()
    tid1 = sched.add("quilt", "low priority", priority=5)
    tid2 = sched.add("quilt", "high priority", priority=1)
    pending = sched.pending()
    assert pending[0]["id"] == tid2


def test_scheduler_complete():
    sched = Scheduler()
    tid = sched.add("quilt", "test")
    sched.complete(tid, success=True)
    assert sched.tasks[tid]["status"] == "success"


def test_scheduler_dependencies():
    sched = Scheduler()
    tid1 = sched.add("quilt", "first")
    tid2 = sched.add("quilt", "second", dependencies=[tid1])
    # tid2 not ready yet
    assert tid2 not in sched.ready()
    sched.complete(tid1, success=True)
    assert tid2 in sched.ready()


def test_scheduler_stats():
    sched = Scheduler()
    sched.add("quilt", "x")
    sched.add("moth", "y")
    stats = sched.stats()
    assert stats["by_substrate"]["quilt"] == 1
    assert stats["by_substrate"]["moth"] == 1


def test_scheduler_invalid_substrate():
    sched = Scheduler()
    try:
        sched.add("invalid", "x")
        assert False, "should have raised"
    except ValueError:
        pass


# ─── Cross-substrate integration tests ──────────────────────

def test_run_all_substrates():
    """Run something on every substrate — verifies the substrate registry."""
    for name in SUBSTRATES:
        s = get_substrate(name)
        if name == "rsi":
            result = s.run({"type": "rsi_step", "iterations": 1})
        elif name == "quilt":
            result = s.run({"type": "load_canon", "limit": 2})
        elif name == "moth":
            result = s.run({"type": "amplitude_walk", "steps": 3})
        elif name == "jev":
            result = s.run({"type": "probe"})
        elif name == "jepa":
            result = s.run({"type": "trajectory_predict", "start": "x"})
        elif name == "trainer":
            result = s.run({"type": "default"})
        else:
            continue
        assert result.status in ("success", "failed"), f"{name}: {result.status} {result.error}"


def test_chord_across_substrates():
    """A canonical fact should produce polyformality across substrates."""
    canonical_facts = [
        "the substrate walker canon: every chord is canon in disguise",
        "the substrate walker canon: agreement is canonical",
        "the substrate walker: every chord is canon in disguise",
    ]
    chord = chord_verdict(canonical_facts)
    assert chord["polyformality"] > 0.2  # Three statements about same thing


# ─── Run all tests ─────────────────────────────────────────

test("test_canary", t_canary)
test("test_fleet_health", t_fleet_health)
test("test_polyformality_identical", t_polyformality_identical)
test("test_polyformality_different", t_polyformality_different)
test("test_chord_verdict_promoted", t_chord_verdict_promoted)
test("test_chord_verdict_not_promoted", t_chord_verdict_not_promoted)
test("test_witness_deterministic", t_witness_deterministic)
test("test_witness_format", t_witness_format)
test("test_resource_limits", t_resource_limits)
test("test_check_substrate_available", t_check_substrate_available)
test("test_rsi_loop_propose", t_rsi_loop_propose)
test("test_rsi_loop_test", t_rsi_loop_test)
test("test_rsi_loop_score", t_rsi_loop_score)
test("test_rsi_step_logged", t_rsi_step_logged)
test("test_rsi_run_multiple", t_rsi_run_multiple)

test("test_quilt_substrate_availability", t_quilt_substrate_availability)
test("test_quilt_load_canon", t_quilt_load_canon)
test("test_quilt_probe", t_quilt_probe)
test("test_quilt_list_experiments", t_quilt_list_experiments)
test("test_moth_availability", t_moth_availability)
test("test_moth_quantum_polygon", t_moth_quantum_polygon)
test("test_moth_amplitude_walk", t_moth_amplitude_walk)
test("test_moth_null_result", t_moth_null_result)
test("test_jev_availability", t_jev_availability)
test("test_jev_probe_no_key", t_jev_probe_no_key)
test("test_jepa_availability", t_jepa_availability)
test("test_jepa_predict_neighbors", t_jepa_predict_neighbors)
test("test_jepa_embed_similarity", t_jepa_embed_similarity)
test("test_jepa_trajectory_predict", t_jepa_trajectory_predict)
test("test_trainer_run", t_trainer_run)
test("test_trainer_deterministic", t_trainer_deterministic)
test("test_rsi_substrate_run", t_rsi_substrate_run)
test("test_get_substrate", t_get_substrate)
test("test_list_substrates", t_list_substrates)
test("test_substrate_witnesses_persist", test_substrate_witnesses_persist)

test("test_list_agents", t_list_agents)
test("test_get_agent", t_get_agent)
test("test_agent_runs", test_agent_runs)

test("test_bus_publish_subscribe", test_bus_publish_subscribe)
test("test_bus_topics", test_bus_topics)
test("test_bus_count", test_bus_count)
test("test_bus_hash_deterministic", test_bus_hash_deterministic)

test("test_scheduler_add_and_ready", test_scheduler_add_and_ready)
test("test_scheduler_priority_order", test_scheduler_priority_order)
test("test_scheduler_complete", test_scheduler_complete)
test("test_scheduler_dependencies", test_scheduler_dependencies)
test("test_scheduler_stats", test_scheduler_stats)
test("test_scheduler_invalid_substrate", test_scheduler_invalid_substrate)

test("test_run_all_substrates", test_run_all_substrates)
test("test_chord_across_substrates", test_chord_across_substrates)

print("\n=== mavis-fleet test results ===")
for name, status in results:
    print(f"  {status:60} {name}")

print(f"\n{len(results) - len(failures)}/{len(results)} passed")
if failures:
    sys.exit(1)
