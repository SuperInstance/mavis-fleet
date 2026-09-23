# mavis-fleet

> Multi-substrate autonomous research & RSI organizational system.

**Rename of `autoclaw`** — comprehensive rebuild for the multi-substrate reality.

The fleet coordinates agents across six substrates:

| Substrate | Purpose |
|-----------|---------|
| **quilt** | Canon substrate: pieces, witnesses, multi-oracle verification |
| **moth** | MOTHQuantum / quantumaudio SDK: quantum polygon experiments |
| **jev** | Joint Embedding Validator oracle gate |
| **jepa** | Joint Embedding Predictive Architecture: cell graph prediction |
| **trainer** | Autoresearch pattern: 5-min experiments on train.py |
| **rsi** | Recursive Self-Improvement: fleet experiments on itself |

Plus 14 agent roles: researcher, teacher, critic, distiller, editor, writer, code_reviewer, consistency, coordinator, project_manager, scientist, strategy, security, pool.

## Quick Start

```bash
# Health
python3 -m fleet health

# Run on a substrate
python3 -m fleet run quilt --type load_canon --arg limit=3
python3 -m fleet run moth --type amplitude_walk
python3 -m fleet run jepa --type trajectory_predict --arg start=02_ode
python3 -m fleet run trainer  # autoresearch pattern
python3 -m fleet run rsi       # meta-substrate

# RSI loop
python3 -m fleet rsi --iterations 5

# Coordination
python3 -m fleet schedule quilt "test tile pipeline"
python3 -m fleet pending
python3 -m fleet publish "doctrine.announced" "cells_are_scars"
python3 -m fleet subscribe --topic doctrine
```

## Tests

```bash
python3 run_tests.py    # 50/50 passing
```

## Substrate Coverage

The substrate walker canon flows across all 6 substrates:
- **quilt** = canon pieces + witness log
- **moth** = cell=amplitude, witness=time register (structural isomorphism)
- **jev** = polyformality-scored canon gate
- **jepa** = substrate walker trajectory prediction
- **trainer** = 5-min time-budgeted experiments
- **rsi** = the system improves itself via proposer → tester → scorer → witness

## Architecture

```
                  ┌─────────────┐
                  │   Bus       │  message bus (JSONL persistence)
                  └─────┬───────┘
                        │
            ┌───────────┼───────────┐
            │           │           │
        ┌───▼──┐   ┌────▼────┐  ┌────▼────┐
        │Quilt │   │  MOTH   │  │  JEV    │  ← substrates
        └──┬───┘   └────┬────┘  └────┬────┘
           │           │           │
        ┌──▼───────────▼───────────▼──┐
        │   Scheduler + RSI Loop     │
        └─────────────┬───────────────┘
                      │
            ┌─────────┼─────────┐
            │   14 Agents        │
            │ (researcher/critic │
            │  etc.)             │
            └────────────────────┘
```

## Bedrock Doctrines

- `cells_are_scars` — every action leaves a witness record
- `witness_log_is_prediction` — runs are auditable
- `canon_gate_is_chord` — promotion requires multi-substrate agreement
- `oracle_is_heard` — multi-oracle verification
- `substrate_quantum` — canon in superposition until observed
- `polyformalism_canary` — same hash across all substrates
