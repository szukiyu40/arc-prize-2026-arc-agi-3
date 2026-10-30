"""Deadline-only overlays for the exact 28.64 runtime; no priority formula edits."""
from __future__ import annotations

import hashlib
from pathlib import Path


EXPECTED = {
    "ARC3-Inference/inference/framework/solver.py": "42b4794f0447e071ba118194c64d009f7fa59df0b84f3d9c35da4dd215824c52",
    "ARC3-Inference/inference/agent/tool_agent.py": "053556f4a2d19bbb0f04d3ecde14bad2d76abfe91e89254740b763136a5a8e82",
    "tufa-arc-agi-framework/src/taaf/benchmark.py": "d273e8056f83a3d1557d31c50c9716ed205258c8b1ba31747367a743d51c9497",
}


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Deadline patch anchor changed: {old[:100]!r}")
    return source.replace(old, new, 1)


def patch_solver(source):
    source = replace_once(source, "from __future__ import annotations\n",
        "from __future__ import annotations\n"
        "from arc3_deadline import get_budget, DeadlineReached, require_work\n")
    source = replace_once(source,
        "    def runtime_limit_reached(self) -> bool:\n",
        "    def runtime_limit_reached(self) -> bool:\n"
        "        if get_budget() is not None and get_budget().remaining_work() <= 0:\n"
        "            return True\n")
    source = replace_once(source,
        '        return {"run_elapsed_seconds": elapsed, "time_remaining_seconds": remaining}\n',
        '        if get_budget() is not None:\n'
        '            shared = get_budget().remaining_work()\n'
        '            remaining = shared if remaining is None else min(remaining, shared)\n'
        '        return {"run_elapsed_seconds": elapsed, "time_remaining_seconds": remaining}\n')
    source = replace_once(source,
        '    def _play_inner(self) -> None:\n        run = self.game.game_run\n',
        '    def _play_inner(self) -> None:\n        run = self.game.game_run\n'
        '        if self.should_stop():\n'
        '            self._finish_if_needed()\n'
        '            return\n')
    source = replace_once(source,
        '        except Exception as exc:\n            if run.final_score is None:\n',
        '        except DeadlineReached:\n'
        '            if run.state == "playing":\n'
        '                run.state = "cancelled"\n'
        '            run.solver_note = "notebook work deadline"\n'
        '        except Exception as exc:\n            if run.final_score is None:\n')
    source = replace_once(source,
        '            if self.stop_event.is_set() and run.state == "playing":\n',
        '            deadline_reached = get_budget() is not None and get_budget().remaining_work() <= 0\n'
        '            if (self.stop_event.is_set() or deadline_reached) and run.state == "playing":\n')
    source = replace_once(source,
        '    def soft_time_remaining_seconds(self) -> float | None:\n',
        '    def soft_time_remaining_seconds(self) -> float | None:\n'
        '        if get_budget() is not None:\n'
        '            return get_budget().remaining_work()\n')
    source = replace_once(source,
        '        timeout = max(0.0, float(self.cancel_drain_timeout_s))\n',
        '        timeout = max(0.0, float(self.cancel_drain_timeout_s))\n'
        '        if get_budget() is not None:\n'
        '            timeout = min(timeout, max(0.0, get_budget().remaining_cleanup()-30.0))\n')
    source = replace_once(source,
        '            analyzer = self._make_analyzer(game, index, local_server)\n',
        '            require_work("game worker")\n'
        '            analyzer = self._make_analyzer(game, index, local_server)\n')
    source = replace_once(source,
        '            session.play()\n        except Exception as exc:\n',
        '            session.play()\n'
        '        except DeadlineReached:\n'
        '            run = game.game_run\n'
        '            if run is not None and run.final_score is None:\n'
        '                if run.state == "playing":\n'
        '                    run.state = "cancelled"\n'
        '                run.solver_note = "notebook work deadline before admission"\n'
        '                game.finish_game()\n'
        '        except Exception as exc:\n')
    return source


def patch_agent(source):
    source = replace_once(source, "from __future__ import annotations\n",
        "from __future__ import annotations\n"
        "from arc3_deadline import get_budget, DeadlineReached, require_work, request_timeouts\n")
    source = replace_once(source,
        '            self._free += 1\n            self._enqueue_and_wait(priority, snapshot)\n',
        '            self._free += 1\n'
        '            try:\n'
        '                self._enqueue_and_wait(priority, snapshot)\n'
        '            except DeadlineReached:\n'
        '                # Restore the caller\'s lease; session.finally releases it once.\n'
        '                self._free -= 1\n'
        '                raise\n')
    source = replace_once(source,
        '        # TEMPORARY: with slots == games nobody should ever block here\n',
        '        require_work("priority admission")\n'
        '        # TEMPORARY: with slots == games nobody should ever block here\n')
    source = replace_once(source,
        '            while token not in self._admitted:\n                self._cond.wait()\n',
        '            while token not in self._admitted:\n'
        '                remaining = None if get_budget() is None else get_budget().remaining_work()\n'
        '                if remaining is not None and remaining <= 0:\n'
        '                    self._waiting = [(p, t) for p, t in self._waiting if t != token]\n'
        '                    heapq.heapify(self._waiting)\n'
        '                    self._snapshots.pop(token, None)\n'
        '                    raise DeadlineReached("notebook work deadline in priority queue")\n'
        '                self._cond.wait(timeout=remaining)\n')
    source = replace_once(source,
        '        self._admitted.discard(token)\n',
        '        self._admitted.discard(token)\n'
        '        if get_budget() is not None and get_budget().remaining_work() <= 0:\n'
        '            self._free += 1\n'
        '            raise DeadlineReached("notebook deadline raced with admission")\n')
    source = replace_once(source,
        '    def _pump(self) -> None:\n',
        '    def _pump(self) -> None:\n'
        '        if get_budget() is not None and get_budget().remaining_work() <= 0:\n'
        '            self._cond.notify_all()\n'
        '            return\n')
    source = replace_once(source,
        '                timeout=(\n'
        '                    _CONNECT_TIMEOUT_SECONDS,\n'
        '                    request_timeout_seconds if request_timeout_seconds is not None else self._timeout,\n'
        '                ),\n',
        '                timeout=request_timeouts(\n'
        '                    _CONNECT_TIMEOUT_SECONDS,\n'
        '                    request_timeout_seconds if request_timeout_seconds is not None else self._timeout,\n'
        '                ),\n')
    return source


def patch_benchmark(source):
    source = replace_once(source, "from __future__ import annotations\n",
        "from __future__ import annotations\nfrom arc3_deadline import get_budget, require_work\n")
    source = replace_once(source,
        '        self.start_time = datetime.now()\n',
        '        require_work("benchmark setup")\n'
        '        self.start_time = datetime.now()\n')
    source = replace_once(source,
        '        played_solver.setup()\n        self.solver_label = played_solver.label\n', '')
    source = replace_once(source,
        '        try:\n            for pass_idx in range(self.n_passes):\n',
        '        try:\n'
        '            played_solver.setup()\n'
        '            self.solver_label = played_solver.label\n'
        '            for pass_idx in range(self.n_passes):\n')
    source = replace_once(source,
        '                for game in self.games:\n                    game_copy = copy.deepcopy(game)\n',
        '                for game in self.games:\n'
        '                    require_work("game setup")\n'
        '                    game_copy = copy.deepcopy(game)\n')
    source = replace_once(source,
        '        # Match local-naive vs UTC against ``soft_end_time``\'s tzinfo.\n',
        '        if get_budget() is not None:\n'
        '            await asyncio.sleep(get_budget().remaining_work())\n'
        '            self._deadline_fired = True\n'
        '            target.cancel()\n'
        '            return\n'
        '        # Match local-naive vs UTC against ``soft_end_time``\'s tzinfo.\n')
    return source


PATCHERS = {
    "ARC3-Inference/inference/framework/solver.py": patch_solver,
    "ARC3-Inference/inference/agent/tool_agent.py": patch_agent,
    "tufa-arc-agi-framework/src/taaf/benchmark.py": patch_benchmark,
}


def apply_overlay(source_root):
    source_root = Path(source_root)
    output = {}
    for rel, expected in EXPECTED.items():
        path = source_root/rel
        original = path.read_bytes()
        if hashlib.sha256(original).hexdigest() != expected:
            raise ValueError(f"Unrecognized baseline runtime: {rel}")
        changed = PATCHERS[rel](original.decode())
        compile(changed, rel, "exec")
        output[rel] = changed
    # Validate every input and patch before changing any file.
    for rel, changed in output.items():
        (source_root/rel).write_text(changed)
    return {rel: hashlib.sha256(text.encode()).hexdigest() for rel, text in output.items()}
