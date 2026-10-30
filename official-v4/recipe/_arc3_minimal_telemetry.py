"""Minimal scheduling timestamps applied AFTER the copied deadline overlay.

Reuses the original telemetry solver anchors, without priority evaluation or
whole-queue payloads. It never imports or runs the instrumented game harness.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


TRACE_HELPER = '''
_ARC3_SCHEDULER_TRACE_LOCK = threading.Lock()
_ARC3_SCHEDULER_TRACE_SEQ = 0
_ARC3_TELEMETRY_ERROR = None


def _arc3_scheduler_trace(kind, **fields):
    trace_path = os.environ.get("ARC3_SCHEDULER_TRACE", "")
    if not trace_path:
        return
    global _ARC3_SCHEDULER_TRACE_SEQ, _ARC3_TELEMETRY_ERROR
    with _ARC3_SCHEDULER_TRACE_LOCK:
        if _ARC3_TELEMETRY_ERROR is not None:
            return
        _ARC3_SCHEDULER_TRACE_SEQ += 1
        before = time.monotonic()
        epoch = time.time()
        after = time.monotonic()
        record = dict(seq=_ARC3_SCHEDULER_TRACE_SEQ, monotonic=before,
                      epoch=epoch, monotonic_after=after,
                      thread=threading.get_ident(), kind=kind, **fields)
        try:
            with open(trace_path, "a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, sort_keys=True) + "\\n")
        except OSError as exc:
            # Do not interrupt a gate mutation or prevent its subsequent pump.
            # The notebook exposes this in-memory failure in the final manifest.
            _ARC3_TELEMETRY_ERROR = {"type": type(exc).__name__, "message": str(exc)[:500],
                                   "failed_seq": _ARC3_SCHEDULER_TRACE_SEQ}


'''


def instrument_agent(text, replace_once):
    text = replace_once(text, "class _PriorityGate:\n", TRACE_HELPER + "class _PriorityGate:\n")
    text = replace_once(text,
        "        heapq.heappush(self._waiting, (-int(priority), token))\n        self._pump()",
        "        heapq.heappush(self._waiting, (-int(priority), token))\n"
        "        _arc3_scheduler_trace('enqueue', token=token, priority=int(priority))\n"
        "        self._pump()")
    # Record successful acquisition only after the deadline-race check.
    text = replace_once(text,
        '            raise DeadlineReached("notebook deadline raced with admission")\n',
        '            raise DeadlineReached("notebook deadline raced with admission")\n'
        "        _arc3_scheduler_trace('acquired', token=token)\n")
    text = replace_once(text,
        '    def release(self) -> None:\n        with self._cond:\n            self._free += 1\n',
        '    def release(self) -> None:\n        with self._cond:\n            self._free += 1\n'
        "            _arc3_scheduler_trace('release', reason='session_finally')\n")
    text = replace_once(text,
        '            self._free += 1\n            try:\n                self._enqueue_and_wait(priority, snapshot)\n',
        '            self._free += 1\n'
        "            _arc3_scheduler_trace('release', reason='handover')\n"
        '            try:\n                self._enqueue_and_wait(priority, snapshot)\n')
    text = replace_once(text,
        '                self._clock_deadline = min(self._clock_deadline, deadline) if self._clock_deadline is not None else deadline\n',
        '                self._clock_deadline = min(self._clock_deadline, deadline) if self._clock_deadline is not None else deadline\n'
        "            _arc3_scheduler_trace('gate_clock', started=self._clock_start, deadline=self._clock_deadline)\n")
    return text


def instrument_solver(text, legacy):
    text = legacy["instrument_solver"](text)
    return legacy["replace_once"](text,
        "            gate.acquire(_PRIORITY_UNTRIMMED_BASE - self._queue_position())\n",
        "            try:\n"
        "                gate.acquire(_PRIORITY_UNTRIMMED_BASE - self._queue_position())\n"
        "            except DeadlineReached as exc:\n"
        "                _arc3_scheduler_trace('session_end', game_id=run.game_id,\n"
        "                                      admission_failed=True, error_type=type(exc).__name__)\n"
        "                raise\n")


def patch_runtime(source_root, expected, legacy):
    """Strictly require the exact deadline-overlay outputs supplied by caller."""
    root = Path(source_root)
    paths = {"agent": "ARC3-Inference/inference/agent/tool_agent.py",
             "solver": "ARC3-Inference/inference/framework/solver.py"}
    inputs = {}
    for kind, rel in paths.items():
        raw = (root / rel).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected[rel]:
            raise ValueError("Telemetry must immediately follow the exact deadline overlay: " + rel)
        inputs[kind] = raw.decode()
    outputs = {"agent": instrument_agent(inputs["agent"], legacy["replace_once"]),
               "solver": instrument_solver(inputs["solver"], legacy)}
    for kind, value in outputs.items():
        compile(value, paths[kind], "exec")
    for kind, value in outputs.items():
        (root / paths[kind]).write_text(value)
    return {paths[kind]: hashlib.sha256(value.encode()).hexdigest()
            for kind, value in outputs.items()}
