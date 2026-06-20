#!/usr/bin/env python3
"""Quality-capture driver: drive the LIVE backend through every tutor route + full
interview and GD sims, dumping the REAL delivered transcripts to /tmp/zidd_quality/
for offline quality auditing.

NOT pass/fail — this captures *what the product actually delivers* (teaching text,
bridge exercises, interviewer questions, GD persona turns, scored recaps) so auditor
agents can judge content/teaching/feedback quality.

Run from Zidd-Backend/ with the venv python (live uvicorn + Ollama must be up):

    ./.venv/bin/python scripts/dev_quality_capture.py

Reuses the exact SSE/HTTP plumbing pattern from dev_learning.py.
"""
from __future__ import annotations

import json
import os
import time
import traceback

import httpx

BASE = "http://127.0.0.1:8000"
SUFFIX = str(int(time.time()))
OUT_DIR = "/tmp/zidd_quality"
os.makedirs(OUT_DIR, exist_ok=True)


# --- SSE parsing (verbatim from dev_learning.py) ---------------------------
def collect_sse(c, method, path, headers=None, json_body=None, timeout=300.0):
    frames = []
    event = None
    data_lines = []

    def flush():
        nonlocal event, data_lines
        if not data_lines and event is None:
            return
        raw = "\n".join(data_lines)
        try:
            payload = json.loads(raw) if raw != "" else None
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
                continue
            if line.startswith("event:"):
                v = line[len("event:"):]
                event = v[1:] if v.startswith(" ") else v
            elif line.startswith("data:"):
                v = line[len("data:"):]
                data_lines.append(v[1:] if v.startswith(" ") else v)
        flush()
    return 200, frames, ""


def tokens_text(frames):
    return "".join(p for (e, p) in frames if e is None and isinstance(p, str))


def typed_events(frames):
    """Return [(event_name, payload)] for every non-token, non-done frame."""
    return [(e, p) for (e, p) in frames if e not in (None, "done")]


def done_frame(frames):
    for e, p in frames:
        if e == "done" and isinstance(p, dict):
            return p
    return None


# --- HTTP helpers ----------------------------------------------------------
def register(c, uid):
    r = c.post("/auth/register", json={"user_id": uid, "password": "pw12345"})
    if r.status_code != 200:
        raise SystemExit(f"FATAL: register {uid} -> {r.status_code} {r.text[:200]}")
    tok = r.json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def start(c, h, uid, node, test_mode=False, confirm=False):
    return c.post(
        "/session/start",
        headers=h,
        json={"user_id": uid, "competency_node": node,
              "test_mode": test_mode, "confirm": confirm},
        timeout=180.0,
    )


def get_state(c, h, sid):
    try:
        r = c.get(f"/session/{sid}/state", headers=h, timeout=30.0)
        return r.json() if r.status_code == 200 else {"_status": r.status_code, "_body": r.text[:200]}
    except Exception as e:  # noqa: BLE001
        return {"_error": repr(e)}


def capture_turn(c, h, sid, user_input, want_state=False):
    """Drive one /session/turn, return a rich transcript dict."""
    rec = {"user_input": user_input}
    t0 = time.time()
    try:
        st, frames, err = collect_sse(
            c, "POST", "/session/turn", headers=h,
            json_body={"session_id": sid, "user_input": user_input},
        )
        rec["status"] = st
        rec["assistant_text"] = tokens_text(frames)
        rec["typed_events"] = typed_events(frames)
        rec["done"] = done_frame(frames)
        rec["err"] = err
    except Exception as e:  # noqa: BLE001
        rec["status"] = "EXC"
        rec["exc"] = repr(e)
        rec["trace"] = traceback.format_exc()[-800:]
    rec["latency_s"] = round(time.time() - t0, 1)
    if want_state:
        rec["state_after"] = get_state(c, h, sid)
    print(f"    turn done ({rec.get('status')}, {rec['latency_s']}s, "
          f"{len(rec.get('assistant_text','') or '')} chars, "
          f"{len(rec.get('typed_events',[]) or [])} typed)")
    return rec


def dump(name, obj):
    path = os.path.join(OUT_DIR, name)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=str)
    print(f"  WROTE {path}")


# --- Capture A: learning loop walks every adaptive route -------------------
def capture_learning(c, h, uid):
    print("\n=== CAPTURE A: learning loop (comm_01, every route) ===")
    NODE = "comm_01_self_intro"
    out = {"module": "communication", "node": NODE, "turns": []}

    r = start(c, h, uid, NODE, test_mode=False)
    out["start_status"] = r.status_code
    if r.status_code != 200:
        out["start_error"] = r.text[:300]
        dump("A_learning.json", out)
        return
    sid = r.json()["session_id"]
    out["session_id"] = sid

    # opening
    st, frames, err = collect_sse(c, "GET", f"/session/{sid}/opening", headers=h)
    out["opening"] = {"status": st, "text": tokens_text(frames), "done": done_frame(frames), "err": err}
    print(f"    opening done ({st}, {len(out['opening']['text'])} chars)")

    # crafted inputs to exercise: teach/challenge, bridge, clarify, redirect, recovery
    probes = [
        ("strong_ontask", "Hi, I'm Abhinav. I'm a backend engineer and I build payment systems used by thousands of people every day."),
        ("very_weak", "idk"),
        ("weak_again", "hmm i am not sure what to say here"),
        ("non_english", "मेरा नाम अभिनव है और मैं एक सॉफ्टवेयर इंजीनियर हूँ"),
        ("off_task_fluent", "Honestly I just really love eating pizza and watching cricket matches on the weekend with my friends."),
        ("strong_recovery", "I'm Abhinav, a backend engineer. I design payment infrastructure, and right now I'm focused on making transactions more reliable."),
    ]
    for label, text in probes:
        print(f"  probe: {label}")
        rec = capture_turn(c, h, sid, text, want_state=True)
        rec["probe"] = label
        out["turns"].append(rec)

    dump("A_learning.json", out)


# --- Capture B: interview TEST sim -----------------------------------------
def capture_interview(c, h, uid):
    print("\n=== CAPTURE B: interview TEST sim (int_01) ===")
    NODE = "int_01_elevator_pitch"
    out = {"module": "interview", "node": NODE, "turns": []}

    r = start(c, h, uid, NODE, test_mode=True)
    out["start_status"] = r.status_code
    if r.status_code != 200:
        out["start_error"] = r.text[:300]
        dump("B_interview.json", out)
        return
    sid = r.json()["session_id"]
    out["session_id"] = sid

    inputs = [
        "Hello, I'm Abhinav, a backend engineer who builds payment systems. My goal is to lead platform reliability work.",
        "My biggest strength is debugging complex distributed systems under pressure. For example, I once traced a payment race condition that was double-charging users.",
        "Um, a weakness... I guess I sometimes take on too much myself instead of delegating.",
        "A time I showed leadership: when our webhook pipeline failed during a launch, I coordinated three engineers, isolated the HMAC mismatch, and shipped a fix within an hour.",
    ]
    for i, text in enumerate(inputs, 1):
        print(f"  sim turn {i}")
        rec = capture_turn(c, h, sid, text)
        out["turns"].append(rec)

    # scored recap
    try:
        er = c.post(f"/session/{sid}/end", headers=h, timeout=300.0)
        out["end"] = {"status": er.status_code,
                      "body": er.json() if er.status_code == 200 else er.text[:500]}
        print(f"    end ({er.status_code})")
    except Exception as e:  # noqa: BLE001
        out["end"] = {"status": "EXC", "exc": repr(e)}
    dump("B_interview.json", out)


# --- Capture C: group-discussion TEST sim ----------------------------------
def capture_gd(c, h, uid):
    print("\n=== CAPTURE C: group-discussion TEST sim (gd_01) ===")
    NODE = "gd_01_stake_position"
    out = {"module": "group_discussion", "node": NODE, "turns": []}

    r = start(c, h, uid, NODE, test_mode=True)
    out["start_status"] = r.status_code
    if r.status_code != 200:
        out["start_error"] = r.text[:300]
        dump("C_gd.json", out)
        return
    sid = r.json()["session_id"]
    out["session_id"] = sid

    inputs = [
        "I'll take a clear stance: remote work is a net positive for productivity, and I think the data backs that up.",
        "To support that, studies during the pandemic showed output stayed flat or rose for knowledge workers, while commute stress dropped sharply.",
        "I want to respond to that point about collaboration. I agree in-person helps, but async tools close most of the gap if teams are disciplined.",
        "Building on what Meera said about culture, I'd add that intentional offsites can give you the bonding without forcing daily commutes.",
    ]
    for i, text in enumerate(inputs, 1):
        print(f"  gd turn {i}")
        rec = capture_turn(c, h, sid, text)
        out["turns"].append(rec)

    try:
        er = c.post(f"/session/{sid}/end", headers=h, timeout=300.0)
        out["end"] = {"status": er.status_code,
                      "body": er.json() if er.status_code == 200 else er.text[:500]}
        print(f"    end ({er.status_code})")
    except Exception as e:  # noqa: BLE001
        out["end"] = {"status": "EXC", "exc": repr(e)}
    dump("C_gd.json", out)


def main():
    with httpx.Client(base_url=BASE, timeout=10.0) as c:
        if c.get("/health").status_code != 200:
            raise SystemExit("FATAL: backend /health != 200 — boot uvicorn first")

    with httpx.Client(base_url=BASE, timeout=60.0) as c:
        uid = f"quality_{SUFFIX}"
        h = register(c, uid)
        print(f"registered {uid}")
        capture_learning(c, h, uid)
        capture_interview(c, h, uid)
        capture_gd(c, h, uid)

    print(f"\nALL CAPTURES WRITTEN to {OUT_DIR}/")
    print("  A_learning.json  B_interview.json  C_gd.json")


if __name__ == "__main__":
    main()
