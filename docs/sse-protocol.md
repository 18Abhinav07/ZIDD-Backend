# Zidd SSE Protocol — v1

Every `/session/turn` and `/session/{id}/opening` response is a
`text/event-stream` connection. This document is the canonical contract
between the backend and the frontend.

---

## Frame Format

All frames follow the standard SSE wire format:

```
[event: <event-name>\n]
data: <JSON-encoded payload>\n
\n
```

Plain token frames have no `event:` line. Named-event frames always have one.

---

## Frame Types

### 1. Token (plain text)

```
data: "Hello, let's"
```

- No `event:` line.
- Payload is a **JSON-encoded string** (double-quoted, escape-safe).
- Tokens arrive one-by-one as the model streams.
- Concatenating all token payloads in order gives the full coach message.
- **Only on**: `/session/turn` (coach response) and `/session/{id}/opening`
  (session-opening message).

### 2. `event: progress_update`

```
event: progress_update
data: {"node_id": "comm_01_self_intro", "mastery": 0.72, "clean_streak": 1, "attempts": 3}
```

Emitted **once per scored turn**, after the last token, before `done`.
Use this to animate the progress bar without a second request.

| Field | Type | Description |
|-------|------|-------------|
| `node_id` | string | Current competency node ID |
| `mastery` | float (0–1) | EMA mastery after this turn |
| `clean_streak` | int | Consecutive passing answers on this node |
| `attempts` | int | Total scored answers on this node so far |

### 3. `event: node_advance`

```
event: node_advance
data: {"from_node": "comm_01_self_intro", "to_node": "comm_02_describe_routine"}
```

Emitted when an answer advances the learner to a new node. This is the **last
content frame** on the turn — the new node's opening is **not** streamed on this
connection. The client should present a "Next Skill" break and fetch the opening
via a separate `GET /session/{id}/opening` call, which streams the new node's
opening as its own message. This keeps the old node's feedback and the new
node's opening in distinct bubbles and prevents level-bleed.

| Field | Type | Description |
|-------|------|-------------|
| `from_node` | string | Node just completed |
| `to_node` | string | Node now active |

### 4. `event: session_recap`

```
event: session_recap
data: {"nodes_completed": ["comm_01_self_intro", "comm_02_describe_routine"], "weaknesses": [...], "avg_score": 0.81}
```

Emitted **instead of** `node_advance` when the learner finishes the last node
in the module (`module_done = true`). Always the last frame before `done`.

| Field | Type | Description |
|-------|------|-------------|
| `nodes_completed` | string[] | Node IDs completed this session, in order |
| `weaknesses` | WeaknessRow[] | Aggregated skill weaknesses (see below) |
| `avg_score` | float (0–1) | Final EMA mastery at session close |

**WeaknessRow shape:**
```json
{"skill_id": "past_simple", "hit_count": 3, "last_raw": "confuses simple past with present perfect"}
```

### 5. `event: game_prompt`

```
event: game_prompt
data: {"sentence": "She ___ to the market yesterday.", "hint": "past simple verb", "context": "practises simple past which you've been dropping"}
```

Emitted **instead of token frames** on scaffold teach turns (learner hit
`DOWN_LADDER_FAILS = 2` consecutive hard fails). No tokens stream; this single
frame IS the turn's content. Render a fill-in-the-blank widget.

The `answer_key` is NOT sent — it stays server-side. The learner's fill is
submitted as normal text on the next turn and scored by the graph.

| Field | Type | Description |
|-------|------|-------------|
| `sentence` | string | Natural sentence with exactly one `___` gap |
| `hint` | string | Grammar/vocab category label (NOT the answer) |
| `context` | string | Why this gap targets the current teaching focus |

### 6. `event: speaker` (TEST mode only)

```
event: speaker
data: {"speaker_id": "persona_arjun", "name": "Arjun"}
```

Emitted at the start of each persona's turn in GD/interview simulations.
Open a new speaker bubble; tokens immediately following belong to this speaker.

| Field | Type | Description |
|-------|------|-------------|
| `speaker_id` | string | Internal persona identifier |
| `name` | string | Display name for the bubble header |

### 7. `event: simulation_state` (TEST mode only)

```
event: simulation_state
data: {"turn": 3, "speaker_id": "gd_a", "tension": 0.45}
```

Emitted once per simulation round (TEST mode only — GD/interview), immediately after the `speaker` frame and before that speaker's token stream. Carries the Director's post-decision snapshot so the UI can show round count and tension.

| Field | Type | Description |
|-------|------|-------------|
| `turn` | int | Round number after the Director's decision |
| `speaker_id` | string | Persona about to speak |
| `tension` | float (0–1) | Director's current tension level |

### 8. `event: adaptation_cue`

```
event: adaptation_cue
data: {"action": "ADVANCE", "band": "stretch", "rationale": "learner is strong, push ahead"}
```

Emitted on advancing coaching turns only — after `progress_update`, before
`node_advance`. Carries the selector's decision so the UI can show a short
"adapting your path" cue before opening the new node. **Never** fires on REPEAT
turns or on module-completion turns (the selector records no selection there).

| Field | Type | Description |
|-------|------|-------------|
| `action` | string | `"ADVANCE"` or `"REMEDIATE"` — how the path adapted |
| `band` | string | `"foundational"` \| `"standard"` \| `"stretch"` — difficulty band for the next node |
| `rationale` | string | Short human-readable reason from the selector |

### 9. `event: done`

```
event: done
data: {"session_id": "...", "competency_node": "comm_02_describe_routine", "current_mastery": 0.72, ...}
```

Always the **last frame** on every turn and opening connection. Contains a
full state snapshot the client can store without a second request.

Full `done` payload shape (all fields always present):

```typescript
{
  session_id: string
  competency_node: string
  node_title: string
  current_mastery: number          // 0–1
  turn_count: number
  last_route: string | null        // "teach" | "bridge" | "strengthen" | "challenge" | "redirect" | "clarify" | "ease" | "module_done"
  last_eval_score: number | null   // 0–1
  bridge_attempts: number
  strengthen_attempts: number
  attempts: number                 // scored answers on current node
  clean_streak: number
  scaffold: number                 // >=1 means learner is on gamified path
  remediation: boolean             // module pass-rate below floor
  module_done: boolean
  phase: string                    // "early" | "mid" | "late" (macro lifecycle)
  level_kind: string               // "intro" | "bridge" | "challenge" (node type)
  tester_level: boolean            // true if last node advance was "clean"
  weaknesses: WeaknessRow[]
  on_task: boolean
  english: boolean
  affect: "neutral" | "frustrated" | "confident" | "confused"
  avatar_emotion: "neutral" | "engaged" | "impressed" | "skeptical" | "empathetic" | "patient" | "concerned"
}
```

---

## Frame Order per Turn

```
/session/turn → POST
  │
  ├── [IF scaffold teach turn]
  │     event: game_prompt  (one frame, no tokens before it)
  │
  ├── [ELSE] token frames (zero or more, streaming)
  │
  ├── event: progress_update  (always, once per scored turn)
  │
  ├── [IF path adapted (ADVANCE/REMEDIATE)]
  │     event: adaptation_cue
  │
  ├── [IF module complete]
  │     event: session_recap
  │
  │   [ELSE IF node advanced]
  │     event: node_advance   (last content frame; opening NOT streamed here —
  │                            client calls GET /opening for the new node)
  │
  └── event: done  (always last)
```

On a **TEST-mode turn** (GD/interview simulation) the coaching frames above
(`progress_update` / `node_advance` / `session_recap` / `game_prompt`) do NOT
fire; instead the per-round sequence repeats once per round:

```
  ├── event: speaker            (one frame, opens the bubble)
  ├── event: simulation_state   (turn count + tension snapshot)
  └── token frames              (this speaker's text)
        ... (repeats per round) ...
  └── event: done  (always last)
```

`/session/{id}/opening` → GET
```
  ├── token frames (opening message)
  └── event: done
```

---

## Ordering Guarantees

1. `done` is always the last frame — never skip waiting for it.
2. `progress_update` always precedes `node_advance` / `session_recap` on the
   same turn.
3. Tokens before `node_advance` belong to the OLD node's feedback. No opening
   tokens follow `node_advance` on the same connection — the new node's opening
   is fetched separately via `GET /session/{id}/opening`.
4. `game_prompt` and token frames are mutually exclusive per turn — never both.
5. `session_recap` and `node_advance` are mutually exclusive — never both.
6. In TEST mode, per round `speaker` precedes `simulation_state`, which
   precedes that speaker's token stream.
7. `adaptation_cue`, when present, comes after `progress_update` and before
   `node_advance`. It is absent on REPEAT turns and on module-completion turns.

---

## Error Behavior

The server never closes the stream mid-turn with an HTTP error (the 200 +
headers are already on the wire). There are two distinct failure paths:

1. **In-band fallback (generation yielded nothing).** If the AI backend produces
   an empty stream, the fallback message
   `"Sorry — I lost my train of thought for a second there. Could you try that once more for me?"`
   is emitted as a normal **token**, and the turn ends normally with `done`.

2. **`event: error` frame (the stream raised).** If the opening/turn generator
   itself throws mid-stream (e.g. the local LLM drops the connection), the server
   emits a named error frame and then still emits the terminal `done` frame so the
   client's streaming lock is always released:

   ```
   event: error
   data: {"error": "stream_failed"}
   ```

   | Field | Type | Description |
   |-------|------|-------------|
   | `error` | string | Machine tag — currently always `"stream_failed"` |

   Clients should surface a brief retry affordance on this frame rather than a
   silently truncated bubble, then wait for `done` as usual.

If `game_prompt` generation fails, the turn falls back to a conversational
token stream (the gamified path degrades gracefully).

---

## Pydantic Schemas

All frame shapes are typed in `app/models.py`:

| Frame | Class |
|-------|-------|
| `game_prompt` | `GamePromptFrame` |
| `node_advance` | `NodeAdvanceFrame` |
| `progress_update` | `ProgressUpdateFrame` |
| `session_recap` | `SessionRecapFrame` |
| `speaker` | `SpeakerFrame` |
| `simulation_state` | `SimulationStateFrame` |
| `adaptation_cue` | `AdaptationCueFrame` |
| `done` | `DoneFrame` |

Use these as the source of truth if this document and the code ever diverge.
