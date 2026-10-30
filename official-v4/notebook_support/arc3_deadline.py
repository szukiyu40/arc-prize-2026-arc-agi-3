"""ARC3 notebook-wide clock and owned-process watchdog (standard library only).

Embedded into the deadline-repair notebook. Importing this module starts nothing.
The watchdog is a separate process so a blocked notebook/event loop cannot extend
the hard boundary. A hard abort is a failure, never a successful submission.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import threading
import time


def clock() -> float:
    # Same timebase as Linux /proc process start ticks, including suspend time.
    if hasattr(time, "CLOCK_BOOTTIME"):
        return time.clock_gettime(time.CLOCK_BOOTTIME)
    return time.monotonic()


class DeadlineReached(TimeoutError):
    """The common work window has ended; finish existing records only."""


@dataclass
class Budget:
    origin: float
    work_deadline: float
    hard_deadline: float
    platform_deadline: float
    clock_origin: str = "first_executable_cell"

    def __post_init__(self):
        values = (self.origin, self.work_deadline, self.hard_deadline, self.platform_deadline)
        if not all(math.isfinite(v) for v in values):
            raise ValueError("Non-finite deadline")
        if not self.origin < self.work_deadline < self.hard_deadline < self.platform_deadline:
            raise ValueError("Expected work < hard < platform deadlines")

    def remaining_work(self) -> float:
        return max(0.0, self.work_deadline - clock())

    def remaining_cleanup(self) -> float:
        return max(0.0, self.hard_deadline - clock())

    def require_work(self, phase="work") -> float:
        remaining = self.remaining_work()
        if remaining <= 0:
            raise DeadlineReached(f"Notebook work deadline reached before {phase}")
        return remaining

    def cap_work_window(self, seconds: float) -> None:
        """Demo-only cap; can shorten the original deadline but never extend it."""
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError("Work window must be positive")
        self.work_deadline = min(self.work_deadline, clock() + seconds)
        self.require_work("benchmark")

    def wall_deadline(self) -> datetime:
        # Compatibility only. Runtime enforcement below always uses monotonic.
        return datetime.now(timezone.utc) + timedelta(seconds=self.remaining_work())

    def snapshot(self) -> dict:
        return dict(origin_monotonic=self.origin, clock_origin=self.clock_origin,
                    work_deadline_monotonic=self.work_deadline,
                    hard_deadline_monotonic=self.hard_deadline,
                    platform_deadline_monotonic=self.platform_deadline,
                    elapsed_seconds=max(0.0, clock()-self.origin),
                    work_remaining_seconds=self.remaining_work(),
                    cleanup_remaining_seconds=self.remaining_cleanup())


ACTIVE_BUDGET: Budget | None = None


def get_budget() -> Budget | None:
    return ACTIVE_BUDGET


def work_remaining() -> float | None:
    return None if ACTIVE_BUDGET is None else ACTIVE_BUDGET.remaining_work()


def require_work(phase="work") -> None:
    if ACTIVE_BUDGET is not None:
        ACTIVE_BUDGET.require_work(phase)


def request_timeouts(connect: float, read: float | None) -> tuple[float, float | None]:
    """Recompute at every HTTP attempt, after queue waits and retry backoff.

    Requests timeouts bound connect/read inactivity, not full streamed response
    duration. Existing stop checks and the independent watchdog also remain needed.
    """
    if ACTIVE_BUDGET is None:
        return connect, read
    remaining = ACTIVE_BUDGET.require_work("model HTTP request")
    return min(connect, remaining), remaining if read is None else min(read, remaining)


def parse_process_stat(text: str) -> tuple[int, int]:
    # comm can contain whitespace or parentheses; fields after its final ')' are
    # state(3), ppid(4), ..., starttime(22).
    rest = text[text.rfind(")")+2:].split()
    return int(rest[1]), int(rest[19])


def make_budget(first_cell_monotonic: float, *, real: bool,
                proc_root: Path = Path("/proc")) -> Budget:
    origin, source = first_cell_monotonic, "first_executable_cell"
    if sys.platform == "linux":
        # Count kernel startup as well. Fail closed on Linux if it cannot be
        # measured, rather than silently granting an extra full nine hours.
        _ppid, ticks = parse_process_stat((proc_root/"self/stat").read_text())
        process_start = ticks / os.sysconf("SC_CLK_TCK")
        if not math.isfinite(process_start) or not 0 < process_start <= first_cell_monotonic:
            raise RuntimeError("Cannot establish kernel process start time")
        origin = min(origin, process_start)
        source = "kernel_process_start_including_time_before_first_cell"
    # Real: work stops at 8h50, hard abort by 8h58; two minutes left for
    # platform overhead. Demo: explicit 180min session, 3min cleanup reserve.
    work, hard, platform = (31800, 32280, 32400) if real else (10620, 10770, 10800)
    budget = Budget(origin, origin+work, origin+hard, origin+platform, source)
    budget.require_work("setup")
    return budget


def _group_exists(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False


def _signal_group(pgid: int, sig: int) -> None:
    try:
        os.killpg(pgid, sig)
    except ProcessLookupError:
        pass


def _start_identity(pid: int) -> int | None:
    if sys.platform == "linux":
        return parse_process_stat(Path(f"/proc/{pid}/stat").read_text())[1]
    return None


def _signal_owned_group(pgid: int, identity: int | None, sig: int) -> None:
    if identity is not None:
        try:
            if _start_identity(pgid) != identity:
                return  # A different process has reused the PID.
        except FileNotFoundError:
            # A session leader can exit before its children. An existing PGID
            # remains reserved by that process group until its last member exits.
            pass
    _signal_group(pgid, sig)


def _descendants(parent: int, exclude: int) -> dict[int, int]:
    """Linux fallback for notebook-owned grandchildren that changed sessions."""
    if sys.platform != "linux":
        return {}
    records = {}
    for directory in Path("/proc").iterdir():
        if not directory.name.isdigit():
            continue
        try:
            records[int(directory.name)] = parse_process_stat((directory/"stat").read_text())
        except (OSError, ValueError, IndexError):
            continue
    parents = {parent}
    descendants = {}
    while True:
        found = {pid for pid, (ppid, _) in records.items()
                 if ppid in parents and pid != exclude and pid not in parents}
        if not found:
            return descendants
        descendants.update({pid: records[pid][1] for pid in found})
        parents.update(found)


def _signal_identities(identities: dict[int, int], sig: int) -> None:
    for pid, start_ticks in identities.items():
        try:
            if parse_process_stat(Path(f"/proc/{pid}/stat").read_text())[1] == start_ticks:
                os.kill(pid, sig)
        except (ProcessLookupError, FileNotFoundError):
            pass


def watchdog_main(settings: dict) -> None:
    parent = int(settings["parent"])
    hard = float(settings["hard_deadline"])
    parent_identity = settings.get("parent_identity")
    grace = min(float(settings.get("kill_grace", 2.0)), max(0.0, hard-clock()))
    terminate_at = min(float(settings["terminate_at"]), hard-grace)
    groups: dict[int, int | None] = {}
    selector = selectors.DefaultSelector()
    selector.register(sys.stdin.fileno(), selectors.EVENT_READ)
    buffer = b""
    os.write(sys.stdout.fileno(), b"READY\n")
    reason = "hard_deadline"
    terminated = killed = False
    children = {}
    while clock() < hard:
        now = clock()
        if not terminated and now >= terminate_at:
            children = _descendants(parent, os.getpid())
            for pgid, identity in groups.items():
                _signal_owned_group(pgid, identity, signal.SIGTERM)
            _signal_identities(children, signal.SIGTERM)
            terminated = True
        if terminated and not killed and now >= terminate_at+grace:
            for pgid, identity in groups.items():
                _signal_owned_group(pgid, identity, signal.SIGKILL)
            _signal_identities(children, signal.SIGKILL)
            killed = True
        next_event = terminate_at if not terminated else (terminate_at+grace if not killed else hard)
        # Periodic wake also handles a suspended Linux host on CLOCK_BOOTTIME.
        ready = selector.select(min(1.0, max(0.0, next_event-clock())))
        if not ready:
            continue
        chunk = os.read(sys.stdin.fileno(), 65536)
        if not chunk:
            reason = "parent_exited"
            break
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            msg = json.loads(line)
            if msg["op"] == "add":
                groups[int(msg["pid"])] = msg["identity"]
            elif msg["op"] == "remove":
                groups.pop(int(msg["pid"]), None)
            elif msg["op"] == "complete":
                if groups:
                    raise RuntimeError("Watchdog cannot disarm with owned groups")
                return
            else:
                raise RuntimeError("Unknown watchdog message")
            os.write(sys.stdout.fileno(), (json.dumps({"ack": msg["op"], "pid": msg["pid"]})+"\n").encode())
    # Capture descendants before killing the parent; never signal the gateway
    # or another notebook. Parent liveness is tied to this private pipe.
    children = _descendants(parent, os.getpid())
    for pgid, identity in groups.items():
        _signal_owned_group(pgid, identity, signal.SIGTERM)
    _signal_identities(children, signal.SIGTERM)
    if reason == "hard_deadline":
        time.sleep(max(0.0, hard-clock()))
    else:
        time.sleep(min(grace, 0.2))
    for pgid, identity in groups.items():
        _signal_owned_group(pgid, identity, signal.SIGKILL)
    _signal_identities(children, signal.SIGKILL)
    if reason == "hard_deadline":
        try:
            if parent_identity is None or _start_identity(parent) == parent_identity:
                os.kill(parent, signal.SIGKILL)
        except (ProcessLookupError, FileNotFoundError):
            pass
    # Diagnostics are intentionally after termination so failed writes cannot
    # delay the hard stop. This is a failure marker, never a submission file.
    try:
        Path(settings["event_path"]).write_text(json.dumps({
            "status": "hard_timeout" if reason == "hard_deadline" else reason,
            "hard_deadline_monotonic": hard, "observed_monotonic": clock(),
            "official_success": False,
        }, indent=2))
    except OSError:
        pass


class Guard:
    def __init__(self, budget: Budget, module_file: Path, event_path: Path,
                 *, kill_grace: float = 2.0):
        self.budget = budget
        self.processes: dict[int, subprocess.Popen] = {}
        self.identities: dict[int, int | None] = {}
        self.threads: list[threading.Thread] = []
        self.closed = False
        settings = dict(parent=os.getpid(), parent_identity=_start_identity(os.getpid()),
                        hard_deadline=budget.hard_deadline,
                        terminate_at=min(budget.work_deadline+180.0, budget.hard_deadline-kill_grace),
                        kill_grace=kill_grace, event_path=str(event_path))
        self.watchdog = subprocess.Popen(
            [sys.executable, str(module_file), "--watchdog", json.dumps(settings)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            start_new_session=True)
        with selectors.DefaultSelector() as selector:
            selector.register(self.watchdog.stdout, selectors.EVENT_READ)
            if not selector.select(min(5.0, budget.require_work("watchdog startup"))):
                self.watchdog.kill()
                self.watchdog.wait(timeout=2)
                raise RuntimeError("Deadline watchdog did not start")
        if self.watchdog.stdout.readline() != b"READY\n":
            raise RuntimeError("Deadline watchdog startup failed")

    def _send(self, op, pid=None, identity=None):
        if self.watchdog.poll() is not None:
            raise RuntimeError("Deadline watchdog exited unexpectedly")
        payload = json.dumps(dict(op=op, pid=pid, identity=identity)).encode()+b"\n"
        self.watchdog.stdin.write(payload)
        self.watchdog.stdin.flush()
        if op != "complete":
            with selectors.DefaultSelector() as selector:
                selector.register(self.watchdog.stdout, selectors.EVENT_READ)
                if not selector.select(min(2.0, self.budget.remaining_cleanup())):
                    raise RuntimeError("Deadline watchdog did not acknowledge process ownership")
            reply = self.watchdog.stdout.readline()
            if not reply or json.loads(reply) != {"ack": op, "pid": pid}:
                raise RuntimeError("Deadline watchdog ownership acknowledgement mismatch")

    def spawn(self, args, **kwargs):
        self.budget.require_work("process launch")
        if self.closed:
            raise RuntimeError("Guard already closed")
        kwargs["start_new_session"] = True
        process = subprocess.Popen(args, **kwargs)
        self.processes[process.pid] = process
        try:
            try:
                identity = _start_identity(process.pid)
            except FileNotFoundError:
                identity = None  # A short-lived child can already have exited.
            self.identities[process.pid] = identity
            self._send("add", process.pid, identity)
        except BaseException:
            _signal_group(process.pid, signal.SIGKILL)
            process.wait(timeout=1)
            raise
        return process

    def run(self, args, *, check=False, capture_output=False, timeout=None,
            input=None, **kwargs):
        remaining = self.budget.require_work("setup command")
        timeout = remaining if timeout is None else min(float(timeout), remaining)
        if capture_output:
            if "stdout" in kwargs or "stderr" in kwargs:
                raise ValueError("capture_output conflicts with stdout/stderr")
            kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if input is not None:
            kwargs["stdin"] = subprocess.PIPE
        process = self.spawn(args, **kwargs)
        try:
            stdout, stderr = process.communicate(input=input, timeout=timeout)
            result = subprocess.CompletedProcess(args, process.returncode, stdout, stderr)
            if check:
                result.check_returncode()
            return result
        finally:
            self.stop_process(process)

    def stop_process(self, process, *, grace=5.0):
        pid = process.pid
        if pid not in self.processes:
            return
        _signal_owned_group(pid, self.identities[pid], signal.SIGTERM)
        end = min(clock()+grace, self.budget.hard_deadline-2.0)
        while clock() < end:
            process.poll()  # Reap the group leader before checking group liveness.
            if not _group_exists(pid):
                break
            time.sleep(min(0.05, max(0.0, end-clock())))
        if _group_exists(pid):
            _signal_owned_group(pid, self.identities[pid], signal.SIGKILL)
        process.wait(timeout=max(0.01, min(1.0, self.budget.remaining_cleanup())))
        reap_end = min(clock()+1.0, self.budget.hard_deadline-1.0)
        while _group_exists(pid) and clock() < reap_end:
            time.sleep(0.01)
        if _group_exists(pid):
            # Leave ownership with the independent watchdog on a stalled exit.
            raise RuntimeError("Owned process group did not exit before cleanup boundary")
        self._send("remove", pid)
        del self.processes[pid]
        del self.identities[pid]

    def track_thread(self, thread):
        self.threads.append(thread)
        return thread

    def cleanup(self):
        """Stop owned serving/setup processes; watchdog remains armed."""
        for process in list(self.processes.values()):
            self.stop_process(process)
        threads = list(dict.fromkeys(self.threads + [
            t for t in threading.enumerate() if t.name.startswith("harness-game")]))
        for thread in threads:
            if thread is threading.current_thread() or thread.ident is None:
                continue
            thread.join(timeout=max(0.0, self.budget.remaining_cleanup()-2.0))
            if thread.is_alive():
                raise RuntimeError("Worker did not finish before cleanup boundary")

    def complete(self):
        """Called by the LAST cell, after summaries and cleanup have finished."""
        self.cleanup()
        if self.budget.remaining_cleanup() <= 2.0:
            raise DeadlineReached("Insufficient margin to disarm watchdog")
        self._send("complete")
        self.watchdog.stdin.close()
        self.watchdog.wait(timeout=min(2.0, self.budget.remaining_cleanup()))
        self.watchdog.stdout.close()
        if self.watchdog.returncode:
            raise RuntimeError("Deadline watchdog did not acknowledge completion")
        self.closed = True


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "--watchdog":
        raise SystemExit("This module is imported by the notebook; only --watchdog is executable")
    watchdog_main(json.loads(sys.argv[2]))
