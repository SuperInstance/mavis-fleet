"""Test suite for mavis-fleet reconciler substrate."""
import sys
sys.path.insert(0, "/workspace/repos/mavis-fleet")

from fleet.substrates import Reconciler, get_substrate, list_substrates


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


def t_list_substrates():
    subs = list_substrates()
    assert "reconciler" in subs
    assert "quilt" in subs
    assert "moth" in subs


def t_reconciler_in_registry():
    r = get_substrate("reconciler")
    assert isinstance(r, Reconciler)
    assert r.name == "reconciler"


def t_reconciler_no_desired():
    r = Reconciler()
    result = r.read("missing-topic")
    assert not result.success


def t_reconciler_set_desired():
    r = Reconciler()
    r.write("canon", {"q01": "value1", "q02": "value2"})
    assert "canon" in r.states
    assert r.states["canon"].desired == {"q01": "value1", "q02": "value2"}


def t_reconciler_observe_actual():
    r = Reconciler()
    r.write("canon", {"q01": "value1"})
    r.observe("canon", {"q01": "value1"})
    assert r.states["canon"].actual == {"q01": "value1"}


def t_reconciler_diff():
    """Compute missing/extra/changed between desired and actual."""
    r = Reconciler()
    diff = r._compute_diff(
        desired={"a": 1, "b": 2, "c": 3},
        actual={"a": 1, "b": 99, "d": 4},
    )
    assert "c" in diff["missing"]
    assert "d" in diff["extra"]
    assert "b" in diff["changed"]
    assert "a" not in diff["changed"]


def t_reconciler_reconcile():
    """Read = reconcile: detect missing/extra/changed, take action."""
    r = Reconciler()
    r.write("canon", {"q01": "canon1", "q02": "canon2"})
    r.observe("canon", {"q01": "canon1"})
    result = r.read("canon")
    assert result.success
    assert "q02" in result.diff["missing"]
    assert "create:q02" in result.actions_taken


def t_reconciler_idempotent():
    """Reconciling twice with no change should be no-op the second time."""
    r = Reconciler()
    r.write("canon", {"q01": "v1"})
    r.observe("canon", {"q01": "v1"})
    r.read("canon")
    state = r.states["canon"]
    assert state.diff["missing"] == []
    assert state.diff["extra"] == []
    assert state.diff["changed"] == []


def t_reconciler_health():
    r = Reconciler()
    r.write("topic1", {"k": "v"})
    r.observe("topic1", {"k": "v"})
    r.read("topic1")
    h = r.health()
    assert "topic1" in h["topics"]
    assert h["total_reconciles"] >= 1


test("test_list_substrates", t_list_substrates)
test("test_reconciler_in_registry", t_reconciler_in_registry)
test("test_reconciler_no_desired", t_reconciler_no_desired)
test("test_reconciler_set_desired", t_reconciler_set_desired)
test("test_reconciler_observe_actual", t_reconciler_observe_actual)
test("test_reconciler_diff", t_reconciler_diff)
test("test_reconciler_reconcile", t_reconciler_reconcile)
test("test_reconciler_idempotent", t_reconciler_idempotent)
test("test_reconciler_health", t_reconciler_health)

print("\n=== mavis-fleet reconciler test results ===")
for name, status in results:
    print(f"  {status:60} {name}")

print(f"\n{len(results) - len(failures)}/{len(results)} passed")
if failures:
    sys.exit(1)
