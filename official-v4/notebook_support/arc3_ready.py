"""ARC3 official readiness within the original notebook deadline. Importing starts no work or network.

Production exchange calls are separate owned processes. Tests inject fakes.
No game framework, model library, or environment implementation is imported.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time

FINAL_SETUP_MARGIN = 15.0
WARMUP_LIMIT = 120.0
FLUSH_LIMIT = 30.0


class ReadinessFailure(RuntimeError):
    pass


def assert_official_mode(value):
    if (value or "").strip().lower() not in {"1", "true"}:
        raise ReadinessFailure("Official execution requires a true competition rerun flag")


def timestamp_bridge(clock=time.monotonic, epoch=time.time):
    before = clock()
    wall = epoch()
    after = clock()
    return {"monotonic_before": before, "epoch": wall, "monotonic_after": after}


def preparation_deadline(budget):
    # Keep a 15 s transition margin, but reserve no new active window.
    return budget.work_deadline - FINAL_SETUP_MARGIN


def ready_before_measurement(budget, process, exchange, emit, *, clock, sleep=time.sleep):
    """Health -> exactly one synthetic completion -> health -> confirmed flush.

    Every call receives a total process timeout and the returned result is
    checked against the same absolute preparation deadline. A late result fails.
    """
    end = preparation_deadline(budget)
    def remaining(phase, cap):
        if process.poll() is not None:
            raise ReadinessFailure("Serving process exited before " + phase)
        available = end - clock()
        if available <= 0:
            raise ReadinessFailure("Original notebook preparation deadline reached before " + phase)
        return min(cap, available)

    def call(kind, cap):
        timeout = remaining(kind, cap)
        started = clock()
        result = exchange(kind, timeout)
        if clock() - started > timeout:
            raise ReadinessFailure(kind + " exceeded its total process time slot")
        remaining(kind + " completion", cap)
        return result

    emit("readiness_start", {"preparation_deadline": end})
    while True:
        try:
            health = call("health", 5.0)
        except (OSError, subprocess.SubprocessError) as exc:
            health = {"status": None, "error_type": type(exc).__name__}
        if health.get("status") == 200:
            emit("health_ready", health)
            break
        sleep(remaining("health retry", 3.0))

    # One request only. A timed-out or malformed completion never gets retried.
    warmup = call("warmup", WARMUP_LIMIT)
    payload = warmup.get("json")
    if warmup.get("status") != 200 or not isinstance(payload, dict):
        raise ReadinessFailure("Synthetic warmup did not return HTTP 200 JSON")
    choices = payload.get("choices", [])
    usage = payload.get("usage")
    tokens = usage.get("completion_tokens") if isinstance(usage, dict) else None
    if (not isinstance(tokens, int) or isinstance(tokens, bool) or tokens <= 0
            or not isinstance(choices, list) or len(choices) != 1
            or not isinstance(choices[0], dict)
            or choices[0].get("finish_reason") not in {"stop", "length"}
            or not isinstance(choices[0].get("message"), dict)):
        raise ReadinessFailure("Synthetic warmup lacks completed choice and actual generated tokens")
    emit("warmup_completed", warmup)
    # The pinned Pennyroyal /health generates a token. It MUST precede the
    # final flush; no HTTP health request may repopulate cache afterward.
    if call("health", 5.0).get("status") != 200:
        raise ReadinessFailure("Server failed health after synthetic warmup")

    flush_end = min(end, clock() + FLUSH_LIMIT)
    while True:
        available = min(remaining("cache flush", FLUSH_LIMIT), flush_end - clock())
        if available <= 0:
            raise ReadinessFailure("Cache flush did not succeed in its 30 s slot")
        flush = call("flush", available)
        if clock() > flush_end:
            raise ReadinessFailure("Cache flush returned after its 30 s slot")
        emit("cache_flush_attempt", flush)
        if flush.get("status") == 200 and flush.get("body", "").startswith("Cache flushed.\n"):
            break
        if flush.get("status") != 400 or flush.get("body") != "Flush cache failed.\n":
            raise ReadinessFailure("Unexpected cache flush response")
        sleep(max(0.0, min(1.0, flush_end - clock())))
    remaining("ready publication", 1.0)  # Process liveness only, no cache-affecting HTTP.
    record = {"confirmed": True, "preparation_deadline": end,
              "ready_clock": clock(), "remaining_work_seconds": budget.work_deadline - clock()}
    emit("server_ready", record)
    return record


def begin_measurement(budget, readiness, *, clock):
    """Use the remaining original work budget, never reset or cap it."""
    if not readiness or readiness.get("confirmed") is not True:
        raise ReadinessFailure("Readiness must be confirmed before measurement")
    if readiness.get("measurement_started"):
        raise ReadinessFailure("Exactly one benchmark run is permitted")
    started = clock()
    if budget.work_deadline - started < FINAL_SETUP_MARGIN:
        raise ReadinessFailure("Insufficient original work budget before benchmark")
    if readiness.get("ready_clock", float("inf")) > started:
        raise ReadinessFailure("Invalid readiness clock order")
    readiness["measurement_started"] = True
    return {"started_clock": started, "deadline_clock": budget.work_deadline,
            "active_window_seconds": budget.work_deadline - started,
            "original_notebook_deadline_preserved": True}


def owned_exchange(guard, module_file, port, model, output_dir):
    """Factory only; no HTTP until the returned function is called on Kaggle."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    sequence = 0
    def exchange(kind, timeout):
        nonlocal sequence
        sequence += 1
        destination = output_dir / (f"{sequence:03d}_{kind}.json")
        result = guard.run([sys.executable, str(module_file), "--http", kind,
                            str(port), model, str(timeout), str(destination)],
                           timeout=timeout, check=True, capture_output=True, text=True)
        return json.loads(destination.read_text())
    return exchange


def cleanup_preparation_failure(guard, write_receipt, failure_guard, *, clock=time.monotonic):
    """Stop every owned process before receipt I/O or thread draining.

    A failed stop is recorded and leaves the independent guard armed. Normal
    completion drains inherited precache threads before disarming both guards.
    The separate failure guard bounds the entire path, including stuck I/O.
    """
    errors = []
    for process in list(guard.processes.values()):
        try:
            guard.stop_process(process, grace=1.0)
        except BaseException as exc:
            errors.append({"type": type(exc).__name__, "error": str(exc)[:500]})
    join_deadline = min(clock()+5.0, failure_guard.budget.hard_deadline-5.0)
    for thread in guard.threads:
        if thread.ident is None:
            continue
        thread.join(timeout=max(0.0, join_deadline-clock()))
        if thread.is_alive():
            errors.append({"type":"StalledPrefetchThread","error":"Owned kernel will exit within failure cleanup boundary"})
    write_receipt(errors)
    if errors:
        raise ReadinessFailure("Cleanup incomplete; short failure watchdog and original guard remain armed")
    guard.complete()
    failure_guard.complete()


def _http_once(kind, port, model, timeout, destination):
    # Runtime-host only. URL is fixed to loopback, with no external networking.
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen
    if kind not in {"health", "warmup", "flush"} or not 1 <= int(port) <= 65535:
        raise ValueError("Invalid local readiness request")
    origin = "http://127.0.0.1:" + str(int(port))
    payload = None
    if kind == "warmup":
        payload = {"model": model,
                   "messages": [{"role": "user", "content": "Reply with OK."}],
                   "max_tokens": 16, "temperature": 0.7, "top_p": 0.95,
                   "top_k": 20, "stream": False,
                   "chat_template_kwargs": {"enable_thinking": True}}
        request = Request(origin + "/v1/chat/completions", data=json.dumps(payload).encode(),
                          headers={"Content-Type": "application/json"}, method="POST")
    else:
        request = Request(origin + ("/health" if kind == "health" else "/flush_cache"), method="GET")
    bridge = timestamp_bridge()
    try:
        response = urlopen(request, timeout=float(timeout))
    except HTTPError as exc:
        response = exc
    with response:
        status, raw = response.status, response.read(65537)
    if len(raw) > 65536:
        raise ReadinessFailure("Unexpected readiness response size")
    record = {"kind": kind, "status": status, "before": bridge,
              "after": timestamp_bridge(), "body": raw.decode("utf-8", errors="replace")}
    if kind == "warmup":
        record.update(request=payload, json=json.loads(raw))
    Path(destination).write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 7 or sys.argv[1] != "--http":
        raise SystemExit("Only runtime-host --http readiness requests are executable")
    _http_once(*sys.argv[2:])
