# P13-T5 Process Churn Metrics (Direct vs Broker)

**Date:** 2026-02-18

## Summary

Measured process churn for 12 short-lived sessions:

| Mode | Sessions | Upstream process starts | Notes |
|------|----------|-------------------------|-------|
| Direct (per-session subprocess baseline) | 12 | 12 | Measured via local Python harness that starts one upstream stub per client session |
| Broker mode (P13 transport/proxy architecture) | 12 | 1 | Validated by `test_broker_mode_launches_upstream_once_for_many_short_lived_clients` |

## Evidence

### Direct-mode baseline command

```bash
python - <<'PY'
import subprocess
import sys
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory(prefix='p13t5-') as tmp:
    script = Path(tmp) / 'direct_mode_stub.py'
    script.write_text(
        'import sys\n'
        'for _ in sys.stdin:\n'
        '    pass\n'
    )

    pids = set()
    for _ in range(12):
        proc = subprocess.Popen(
            [sys.executable, '-u', str(script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        proc.communicate(input='{"jsonrpc":"2.0","id":1}\n', timeout=2)
        pids.add(proc.pid)

    print(f'direct_mode_process_starts={len(pids)}')
PY
```

Output:

```text
direct_mode_process_starts=12
```

### Broker-mode evidence

`tests/integration/test_broker_multi_client.py::test_broker_mode_launches_upstream_once_for_many_short_lived_clients`
asserts `launch_count == 1` after 12 short-lived client sessions.

## Interpretation

For equivalent short-lived session count (N=12), broker mode reduced upstream starts from 12 to 1 (91.7% reduction), which directly addresses upstream churn that contributes to repeated authorization prompts.
