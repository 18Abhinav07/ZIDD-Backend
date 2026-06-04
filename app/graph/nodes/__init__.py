"""Graph nodes — decision/prompt-build only. No token streaming here.

Each pedagogy node sets `state["pending"]` to a GenSpec; the service layer
streams it over SSE *after* the graph returns. This keeps the graph pure and
fully mockable (tests monkeypatch app.ai.calls, never touch the network).
"""
