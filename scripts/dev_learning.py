#!/usr/bin/env python3
"""M4 — learning-loop E2E driver against a LIVE localhost backend (Ollama backend).

Self-asserting. Exit 0 only when every checklist item passes. Uses REAL JWTs minted
via POST /auth/register (the middleware test_token bypass CANNOT fire in a real uvicorn
boot), so this exercises the genuine HS256 verify path the deployed app uses.

Run from Zidd-Backend/ with the venv python so the relative .zidd_local.db resolves to
the same store uvicorn writes:

    ./.venv/bin/python scripts/dev_learning.py

Covers (plan M4 Verification, learning loop):
  Item 9   Start a plain tutor session (comm_01 PREP) -> opening streams real tokens
           over SSE, a turn streams adaptive content, NO persona/speaker frames.
  Item 10  Interview TEST sim (int_01, test_mode) -> Director emits a `speaker` frame
           with a name + a `simulation_state` frame (turn/speaker_id/tension), persona
           text streams, and POST /session/{id}/end returns a non-empty summary.
  Item 11  After the sim, a fresh plain tutor turn for the SAME user shows NO `speaker`
           frame and NO persona-name bracket prefix in the assistant text (the
           speaker-bleed fix holds).

The qwen2.5:14b local generation is slow; turn/end calls use generous (300s) timeouts.
"""
from __future__ import annotations

import json
import time

import httpx

BASE = "http://127.0.0.1:8000"
SUFFIX = str(int(time.time()))  # unique per run -> fresh balances, no collisions

# Persona-name prefixes the server formats as "\n[{name}]: " in TEST mode. A plain
# (non-sim) tutor turn must contain NONE of these (the speaker-bleed regression guard).
_PERSONA_PREFIXES = (
    "[Interviewer]:",
    "[Moderator]:",
    "[Aarav]:",
    "[Meera]:",
    "[Kabir]:",
    "[Examiner]:",
)

# --- assertion bookkeeping -------------------------------------------------
_failures: list[str] = []
_passes = 0


def check(label: str, cond: bool, detail: str = "") -> bool:
    global _passes
    if cond:
        _passes += 1
        print(f"  PASS  {label}")
    else:
        _failures.append(label)
        print(f"  FAIL  {label}   {detail}")
    return cond


def section(name: str) -> None:
    print(f"\n=== {name} ===")


# --- SSE parsing -----------------------------------------------------------
def collect_sse(
    c: httpx.Client,
    method: str,
    path: str,
    headers: dict | None = None,
    json_body: dict | None = None,
    timeout: float = 300.0,
) -> tuple[int, list[tuple[str | None, object]], str]:
    """Stream an SSE endpoint to completion; return (status, frames, err_text).

    Each frame is (event, payload): event is None for a default token frame (the
    SSE "message" event), else the typed event name ("speaker", "done", ...).
    payload is json.loads of the `data:` field — a str for token frames, a dict
    for typed/snapshot frames. Mirrors the server's _sse() byte format exactly:
    "event: <name>\\n" (optional) + "data: <json>\\n\\n", one leading space per
    SSE field that the parser strips.

    `headers` MUST carry the Authorization bearer — /opening and /turn are NOT
    JWT-exempt, so a stream opened without it 401s before any frame is written.
    """
    frames: list[tuple[str | None, object]] = []
    event: str | None = None
    data_lines: list[str] = []

    def flush() -> None:
        nonlocal event, data_lines
        if not data_lines and event is None:
            return
        raw = "\n".join(data_lines)
        try:
            payload: object = json.loads(raw) if raw != "" else None
        except json.JSONDecodeError:
            payload = raw
        frames.append((event, payload))
        event = None
        data_lines = []

    with c.stream(method, path, headers=headers, json=json_body, timeout=timeout) as r:
        if r.status_code != 200:
            r.read()
            return r.status_code, frames, r.text[:300]
        for line in r.iter_lines():
            if line == "":
                flush()
                continue
            if line.startswith(":"):
                continue  # SSE comment / keep-alive
            if line.startswith("event:"):
                v = line[len("event:") :]
                event = v[1:] if v.startswith(" ") else v
            elif line.startswith("data:"):
                v = line[len("data:") :]
                data_lines.append(v[1:] if v.startswith(" ") else v)
        flush()  # final frame if the stream ended without a trailing blank line
    return 200, frames, ""


def tokens_text(frames: list[tuple[str | None, object]]) -> str:
    """Concatenate every default token frame (event is None, payload is a str)."""
    return "".join(p for (e, p) in frames if e is None and isinstance(p, str))


def events_of(frames: list[tuple[str | None, object]], name: str) -> list[object]:
    return [p for (e, p) in frames if e == name]


def done_frame(frames: list[tuple[str | None, object]]) -> dict | None:
    for e, p in frames:
        if e == "done" and isinstance(p, dict):
            return p
    return None


# --- HTTP helpers ----------------------------------------------------------
def register(c: httpx.Client, uid: str) -> dict:
    r = c.post("/auth/register", json={"user_id": uid, "password": "pw12345"})
    if r.status_code != 200:
        raise SystemExit(f"FATAL: register {uid} -> {r.status_code} {r.text[:200]}")
    tok = r.json()["access_token"]
    return {"h": {"Authorization": f"Bearer {tok}"}, "uid": uid}


def start(
    c: httpx.Client,
    h: dict,
    uid: str,
    node: str,
    test_mode: bool = False,
    confirm: bool = False,
) -> httpx.Response:
    return c.post(
        "/session/start",
        headers=h,
        json={
            "user_id": uid,
            "competency_node": node,
            "test_mode": test_mode,
            "confirm": confirm,
        },
        timeout=180.0,
    )


def end(c: httpx.Client, h: dict, session_id: str) -> httpx.Response:
    return c.post(f"/session/{session_id}/end", headers=h, timeout=300.0)


# --------------------------------------------------------------------------
def item_9_plain_tutor(c: httpx.Client, h: dict, uid: str) -> None:
    section("Item 9 — plain tutor session: opening + adaptive turn over SSE")
    NODE = "comm_01_self_intro"  # order[0] free taste, PREP coaching node

    r = start(c, h, uid, NODE, test_mode=False, confirm=False)
    if not check("9.1 comm_01 start -> 200", r.status_code == 200, f"got {r.status_code} {r.text[:160]}"):
        return
    sid = r.json()["session_id"]

    # Opening: streamed via Gemini -> fast, real tokens.
    st, frames, err = collect_sse(c, "GET", f"/session/{sid}/opening", headers=h)
    check("9.2 opening stream -> 200", st == 200, err)
    op_text = tokens_text(frames)
    check("9.3 opening streamed non-empty tokens", len(op_text.strip()) > 0, f"got {op_text!r}")
    dn = done_frame(frames)
    check("9.4 opening terminal `done` carries matching session_id",
          dn is not None and dn.get("session_id") == sid, f"got {dn}")

    # Adaptive turn: routes through the LangGraph tutor (Ollama) -> slow.
    st, frames, err = collect_sse(
        c, "POST", "/session/turn", headers=h,
        json_body={"session_id": sid,
                   "user_input": "Hi, my name is Abhinav and I work as a software engineer."},
    )
    check("9.5 turn stream -> 200", st == 200, err)
    turn_text = tokens_text(frames)
    typed = [e for (e, _p) in frames if e not in (None, "done")]
    check("9.6 turn produced adaptive content (tokens or typed event)",
          len(turn_text.strip()) > 0 or len(typed) > 0, f"tokens={turn_text[:80]!r} typed={typed}")
    check("9.7 turn terminal `done` matches session_id",
          (df := done_frame(frames)) is not None and df.get("session_id") == sid, f"got {done_frame(frames)}")
    check("9.8 plain turn emitted NO `speaker` frame", len(events_of(frames, "speaker")) == 0,
          f"got {events_of(frames, 'speaker')}")


def item_10_interview_sim(c: httpx.Client, h: dict, uid: str) -> None:
    section("Item 10 — interview TEST sim: Director speaker + simulation_state + scored end")
    NODE = "int_01_elevator_pitch"  # attempt-metered; 1st attempt is free

    r = start(c, h, uid, NODE, test_mode=True, confirm=False)
    if not check("10.1 int_01 test_mode start -> 200 (1st attempt free)",
                 r.status_code == 200, f"got {r.status_code} {r.text[:200]}"):
        return
    sid = r.json()["session_id"]

    st, frames, err = collect_sse(
        c, "POST", "/session/turn", headers=h,
        json_body={"session_id": sid,
                   "user_input": "Hello, I'm Abhinav, a backend engineer who builds payment systems."},
    )
    check("10.2 sim turn stream -> 200", st == 200, err)

    speakers = events_of(frames, "speaker")
    check("10.3 >=1 `speaker` frame with a name",
          len(speakers) >= 1 and all(isinstance(s, dict) and s.get("name") for s in speakers),
          f"got {speakers}")

    sim_states = events_of(frames, "simulation_state")
    check("10.4 >=1 `simulation_state` frame (turn/speaker_id/tension)",
          len(sim_states) >= 1 and all(
              isinstance(s, dict) and {"turn", "speaker_id", "tension"} <= set(s.keys())
              for s in sim_states),
          f"got {sim_states}")

    persona_text = tokens_text(frames)
    check("10.5 persona text streamed (non-empty)", len(persona_text.strip()) > 0,
          f"got {persona_text[:80]!r}")
    check("10.6 sim turn terminal `done` matches session_id",
          (df := done_frame(frames)) is not None and df.get("session_id") == sid,
          f"got {done_frame(frames)}")

    er = end(c, h, sid)
    check("10.7 end sim session -> 200", er.status_code == 200, f"got {er.status_code} {er.text[:160]}")
    if er.status_code == 200:
        summary = er.json().get("summary", "")
        check("10.8 end returns non-empty summary string",
              isinstance(summary, str) and len(summary.strip()) > 0, f"got {summary!r}")


def item_11_speaker_bleed(c: httpx.Client, h: dict, uid: str) -> None:
    section("Item 11 — post-sim plain turn shows NO stale persona name (bleed fix holds)")
    NODE = "comm_01_self_intro"  # free taste; plain (non-sim) coaching node

    r = start(c, h, uid, NODE, test_mode=False, confirm=False)
    if not check("11.1 fresh plain comm_01 start -> 200", r.status_code == 200,
                 f"got {r.status_code} {r.text[:160]}"):
        return
    sid = r.json()["session_id"]

    st, frames, err = collect_sse(
        c, "POST", "/session/turn", headers=h,
        json_body={"session_id": sid,
                   "user_input": "Let me tell you about my morning routine. I wake up early and exercise."},
    )
    check("11.2 plain turn stream -> 200", st == 200, err)
    check("11.3 NO `speaker` frame on a plain node", len(events_of(frames, "speaker")) == 0,
          f"got {events_of(frames, 'speaker')}")

    text = tokens_text(frames)
    bled = [p for p in _PERSONA_PREFIXES if p in text]
    check("11.4 assistant text carries no persona-name bracket prefix", not bled,
          f"bled prefixes={bled} in {text[:120]!r}")


def main() -> int:
    try:
        with httpx.Client(base_url=BASE, timeout=10.0) as c:
            if c.get("/health").status_code != 200:
                raise SystemExit("FATAL: backend /health != 200 — boot uvicorn from Zidd-Backend/ first")
    except httpx.ConnectError:
        raise SystemExit("FATAL: backend not reachable at 127.0.0.1:8000 — boot uvicorn first")

    with httpx.Client(base_url=BASE, timeout=60.0) as c:
        u = register(c, f"e2e_learn_{SUFFIX}")
        h, uid = u["h"], u["uid"]
        item_9_plain_tutor(c, h, uid)
        item_10_interview_sim(c, h, uid)
        item_11_speaker_bleed(c, h, uid)

    section("RESULT")
    total = _passes + len(_failures)
    print(f"  {_passes}/{total} checks passed")
    if _failures:
        print("  FAILURES:")
        for f in _failures:
            print(f"    - {f}")
        return 1
    print("  ALL GREEN — M4 learning loop verified end-to-end on localhost.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
