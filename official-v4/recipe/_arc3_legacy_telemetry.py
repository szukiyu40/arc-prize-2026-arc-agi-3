"""Add demo-only scheduling telemetry to a copy of the pinned ARC3 harness.

This never changes the preserved upstream source or runs a model. Notebook code
calls this only in demo mode, before importing the copied harness.
"""
from pathlib import Path


TRACE_HELPER = '''
_ARC3_SCHEDULER_TRACE_LOCK = threading.Lock()
_ARC3_SCHEDULER_TRACE_SEQ = 0


def _arc3_scheduler_trace(kind, **fields):
    trace_path = os.environ.get("ARC3_SCHEDULER_TRACE", "")
    if not trace_path:
        return
    global _ARC3_SCHEDULER_TRACE_SEQ
    with _ARC3_SCHEDULER_TRACE_LOCK:
        _ARC3_SCHEDULER_TRACE_SEQ += 1
        record = dict(seq=_ARC3_SCHEDULER_TRACE_SEQ, monotonic=time.monotonic(),
                      thread=threading.get_ident(), kind=kind, **fields)
        with open(trace_path, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\\n")


def _arc3_snapshot_record(snapshot):
    if snapshot is None:
        return None
    return dict(level=snapshot.level, actions=snapshot.actions, tokens=snapshot.tokens,
                cost_multiplier=snapshot.cost_multiplier, total_levels=snapshot.total_levels)


'''

OLD_PRIORITY = '''        return priority_value(
            snapshot, endgame=endgame, tail_fraction=tail_fraction,
            human_actions=_priority_human_actions(), action_scale=_priority_action_scale(),
            token_scale=_priority_token_scale(), action_weight=_priority_action_weight(),
            tail_base=_priority_tail_base(), tail_cap=_priority_tail_cap(),
            **_priority_level_options(),
        )'''

NEW_PRIORITY = '''        options = dict(
            endgame=endgame, tail_fraction=tail_fraction,
            human_actions=_priority_human_actions(), action_scale=_priority_action_scale(),
            token_scale=_priority_token_scale(), action_weight=_priority_action_weight(),
            tail_base=_priority_tail_base(), tail_cap=_priority_tail_cap(),
            **_priority_level_options(),
        )
        value = priority_value(snapshot, **options)
        _arc3_scheduler_trace("priority", snapshot_id=id(snapshot),
                              snapshot=_arc3_snapshot_record(snapshot), options=options,
                              evaluated_at=now, value=value)
        return value'''


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Expected exactly one telemetry anchor: {old[:70]!r}")
    return text.replace(old, new, 1)


def instrument_agent(text):
    text = replace_once(text, "class _PriorityGate:\n", TRACE_HELPER + "class _PriorityGate:\n")
    text = replace_once(text, OLD_PRIORITY, NEW_PRIORITY)
    text = replace_once(text,
        "        heapq.heappush(self._waiting, (-int(priority), token))\n        self._pump()",
        "        heapq.heappush(self._waiting, (-int(priority), token))\n"
        "        _arc3_scheduler_trace(\"enqueue\", token=token, priority=int(priority),\n"
        "                              snapshot_id=id(snapshot) if snapshot is not None else None,\n"
        "                              snapshot=_arc3_snapshot_record(snapshot))\n"
        "        self._pump()")
    text = replace_once(text,
        "        self._admitted.discard(token)\n",
        "        self._admitted.discard(token)\n"
        "        _arc3_scheduler_trace(\"acquired\", token=token)\n")
    text = replace_once(text,
        "            _, token = heapq.heappop(self._waiting)\n",
        "            _arc3_scheduler_trace(\"decision\", queue=[\n"
        "                dict(token=t, priority=-p) for p, t in sorted(self._waiting)])\n"
        "            chosen_priority, token = heapq.heappop(self._waiting)\n"
        "            _arc3_scheduler_trace(\"admit\", token=token, priority=-chosen_priority)\n")
    return text


def instrument_solver(text):
    # The helper is imported from the same patched module as the original gate.
    text = replace_once(text, "    _priority_gate,\n", "    _priority_gate,\n    _arc3_scheduler_trace,\n")
    text = replace_once(text,
        "        gate = _priority_gate()\n        if gate is not None:\n",
        "        _arc3_scheduler_trace(\"session_begin\", game_id=run.game_id,\n"
        "                              game_index=self.game_index, pass_index=self.pass_index)\n"
        "        gate = _priority_gate()\n        if gate is not None:\n")
    text = replace_once(text,
        "        finally:\n            if gate is not None:\n                gate.release()\n",
        "        finally:\n            _arc3_scheduler_trace(\"session_end\", game_id=run.game_id)\n"
        "            if gate is not None:\n                gate.release()\n")
    return text


def patch_runtime(source_root):
    root = Path(source_root)
    agent_path = root / "inference/agent/tool_agent.py"
    solver_path = root / "inference/framework/solver.py"
    # Validate both transformations before writing either file.
    agent = instrument_agent(agent_path.read_text())
    solver = instrument_solver(solver_path.read_text())
    compile(agent, str(agent_path), "exec")
    compile(solver, str(solver_path), "exec")
    agent_path.write_text(agent)
    solver_path.write_text(solver)
