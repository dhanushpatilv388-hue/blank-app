"""
FreeLLMAPI Chat — a friendly front-end for a local FreeLLMAPI router.

You do NOT need to understand this file. Just:
    1. Start FreeLLMAPI on your laptop (see GUIDE.md)
    2. Run this app:  streamlit run streamlit_app.py
    3. Paste your unified API key in the sidebar

Everything is in plain English on purpose: the errors tell you what to fix.
"""

import json
import os

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

DEFAULT_BASE = os.environ.get("FREELLMAPI_BASE_URL", "http://localhost:3001/v1")

# What "auto" means, in human words
MODEL_HELP = {
    "auto": "Let the router pick the best free model right now (recommended)",
    "auto:fast": "Prefer the quickest model — good for short questions",
    "auto:smart": "Prefer the most capable model — good for hard questions",
    "fusion": "Ask several models in parallel, then merge the answers (slower, stronger)",
}

SETUP_STEPS = """
### 1. Start the router on your laptop
Pick ONE of these. You only do this once.

| If you... | Do this |
|---|---|
| Have Windows | Download the **FreeLLMAPI `.exe` installer** from the Releases page, install it, then click the tray icon → **Open Dashboard**. |
| Have a Mac | Download the **`.dmg`** (arm64 for Apple Silicon, x64 for Intel) from Releases, install, open it, tray icon → **Open Dashboard**. |
| Prefer Docker | Run the one-line installer in a terminal: `curl -fsSL https://freellmapi.co/install.sh \\| bash` then open <http://localhost:3001>. |

The dashboard opens at **http://127.0.0.1:31415** (desktop app) or **http://localhost:3001** (Docker).

### 2. Add at least one free provider key
In the dashboard go to **Keys**. The two easiest free keys:

- **Google AI Studio** — <https://aistudio.google.com/apikey> → "Create API key" (free, no card)
- **Groq** — <https://console.groq.com/keys> → "Create API Key" (free, no card)

Paste a key, save, done. Repeat for any other providers you have. More keys = more free tokens.

### 3. Copy your *unified* API key
On the **Keys** page header there is one key that starts with `freellmapi-…`.
That single key is all this app needs — it hides all your provider keys.

### 4. Paste it in the sidebar
Choose where your router is running, paste the `freellmapi-…` key, press **Test connection**.
The base URL must end in `/v1`:

- Desktop app → `http://127.0.0.1:31415/v1` (if it says another port in the tray, use that one)
- Docker / one-liner → `http://localhost:3001/v1`

### 5. Chat
Type in the box at the bottom. The little label under each answer tells you
which free provider actually answered — the router switches automatically when
one hits its limit.

> **Your key stays on your laptop.** This app talks straight to your local
> router and never sends anything to us. The key is only kept in this browser
> tab's memory; it is not written to any file.
"""

# A tiny stand-in catalogue so people can see the interface before installing anything.
DEMO_MODELS = [
    "auto",
    "auto:fast",
    "auto:smart",
    "google/gemini-2.5-flash",
    "groq/llama-3.3-70b",
    "cerebras/qwen3-235b",
    "mistral/mistral-small",
]

DEMO_REPLY = (
    "**This is demo mode — no AI was called.**\n\n"
    "You're seeing the shape of a real reply: streaming text, a provider label underneath, "
    "and your chat history kept in this tab. Nothing was sent anywhere and no key was used.\n\n"
    "To get real answers:\n\n"
    "1. Start FreeLLMAPI on this laptop (desktop app, or the Docker one-liner).\n"
    "2. Add one free provider key on its **Keys** page.\n"
    "3. Turn demo mode **off** in the sidebar, paste your `freellmapi-…` key, "
    "press **Test connection**.\n\n"
    "Then ask me anything — this exact box becomes a real chat."
)

TROUBLE = [
    (
        "Can't reach the router / connection refused",
        "The router isn't running, or the port is wrong. Open the desktop app (or run "
        "`docker compose up -d`) and check the port. Desktop app = 31415, Docker = 3001.",
    ),
    (
        "401 / invalid API key",
        "You pasted a *provider* key instead of the unified `freellmapi-…` key. "
        "Copy it from the top of the Keys page in the dashboard.",
    ),
    (
        "429 / rate limited",
        "Every model you have keys for is at its free limit right now. Add another "
        "provider key, or wait for the reset. Using `auto` lets the router dodge "
        "limits for you.",
    ),
    (
        "No models listed",
        "The router is running but you haven't added any provider keys yet. "
        "Add one on the Keys page, then press Test connection again.",
    ),
    (
        "Answer takes forever / times out",
        "Free models queue under load. Try `auto:fast`, or a smaller model from the list.",
    ),
]


def normalise_base(url: str) -> str:
    """Turn whatever the user typed into a clean '.../v1' base URL."""
    url = (url or "").strip().rstrip("/")
    if not url:
        return DEFAULT_BASE
    if url.endswith("/chat/completions"):
        url = url[: -len("/chat/completions")]
    if not url.endswith("/v1"):
        url = url + "/v1"
    return url


def friendly_error(exc: Exception | None = None, status: int | None = None) -> str:
    """Translate technical failures into something a non-coder can act on."""
    if exc is not None:
        text = str(exc).lower()
        if isinstance(exc, requests.exceptions.ConnectTimeout) or "connection" in text or "refused" in text:
            return (
                "**The router isn't answering.** Is FreeLLMAPI actually running?\n\n"
                "Open the desktop app (or start Docker) and check the port in the "
                "sidebar — desktop app uses `31415`, Docker uses `3001`."
            )
        if "timed out" in text or isinstance(exc, requests.exceptions.ReadTimeout):
            return "**The model took too long.** Free models queue up. Try again, or pick `auto:fast`."
        return f"**Something went wrong:** {exc}"
    if status == 401:
        return (
            "**Key rejected (401).** That looks like a provider key. You need the "
            "unified `freellmapi-…` key from the top of the **Keys** page."
        )
    if status == 403:
        return "**Access denied (403).** Check the key is enabled and the router allows this client."
    if status == 404:
        return (
            "**Endpoint not found (404).** The base URL probably has one `/v1` too many or too few. "
            "It should look like `http://localhost:3001/v1`."
        )
    if status == 429:
        return (
            "**All free limits hit (429).** Add another provider key in the dashboard, "
            "or wait for the quota to reset. `auto` will retry other providers first."
        )
    if status and status >= 500:
        return "**The router or the provider had an internal error.** Try again in a few seconds."
    return f"**Unexpected response** (HTTP {status})."


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------


def list_models(base: str, key: str, timeout: int = 15) -> tuple[list[str], str | None]:
    """Return the model ids the router knows about, or a friendly error."""
    try:
        r = requests.get(
            f"{base}/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001 - we surface a friendly message
        return [], friendly_error(exc=exc)
    if r.status_code != 200:
        return [], friendly_error(status=r.status_code)
    try:
        payload = r.json()
    except ValueError:
        return [], "The router sent something that isn't JSON. Check the base URL."
    items = payload.get("data") if isinstance(payload, dict) else payload
    ids: list[str] = []
    for item in items or []:
        if isinstance(item, dict):
            mid = item.get("id") or item.get("model")
            if mid:
                ids.append(str(mid))
        elif isinstance(item, str):
            ids.append(item)
    return sorted(set(ids)), None


def stream_chat(base: str, key: str, model: str, messages: list[dict], temperature: float):
    """Yield text chunks. Raises ApiError with a friendly message on failure."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
    }
    try:
        r = requests.post(
            f"{base}/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                # Ask the router to report which provider served the request
                "X-FreeLLMAPI-Return-Route": "1",
            },
            json=payload,
            stream=True,
            timeout=(10, 300),
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(friendly_error(exc=exc)) from exc

    if r.status_code != 200:
        detail = ""
        try:
            body = r.json()
            detail = body.get("error", {}).get("message") if isinstance(body, dict) else ""
        except Exception:  # noqa: BLE001
            detail = (r.text or "")[:300]
        msg = friendly_error(status=r.status_code)
        if detail:
            msg += f"\n\n*Router said:* `{detail}`"
        raise RuntimeError(msg)

    routed = r.headers.get("x-routed-via") or r.headers.get("X-Routed-Via")
    yield ("meta", routed)

    for raw in r.iter_lines(decode_unicode=True):
        if not raw:
            continue
        line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data in ("[DONE]", ""):
            if data == "[DONE]":
                break
            continue
        try:
            chunk = json.loads(data)
        except ValueError:
            continue
        if isinstance(chunk, dict) and chunk.get("error"):
            err = chunk["error"]
            raise RuntimeError(f"**The provider rejected the request:** {err.get('message', err)}")
        for choice in chunk.get("choices", []) or []:
            piece = (choice.get("delta") or {}).get("content")
            if piece:
                yield ("text", piece)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

st.set_page_config(page_title="FreeLLMAPI Chat", page_icon="🆓", layout="wide")

st.markdown(
    """
    <style>
      .block-container {padding-top: 2.2rem; max-width: 1050px;}
      .route-chip {display:inline-block; padding:2px 10px; border-radius:999px;
                   background:#eef2ff; color:#3730a3; font-size:.78rem; font-weight:600;}
      .hero {background:linear-gradient(135deg,#4f46e5,#0ea5e9); color:#fff;
             padding:26px 28px; border-radius:16px; margin-bottom:18px;}
      .hero h1 {margin:0 0 6px 0; font-size:1.9rem;}
      .hero p {margin:0; opacity:.92;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>🆓 FreeLLMAPI Chat</h1>
      <p>One chat window for all your free AI models — it picks whichever free model still has quota.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------- sidebar ----------------
with st.sidebar:
    st.header("1. Connect")
    preset = st.radio(
        "Where is FreeLLMAPI running?",
        options=[
            "Desktop app (port 31415)",
            "Docker / installer (port 3001)",
            "Somewhere else",
        ],
        index=0,
    )
    if preset.startswith("Desktop"):
        base_default = "http://127.0.0.1:31415/v1"
    elif preset.startswith("Docker"):
        base_default = "http://localhost:3001/v1"
    else:
        base_default = DEFAULT_BASE

    base_url = st.text_input("Router address", value=base_default, help="Must end in /v1")
    api_key = st.text_input(
        "Unified API key",
        value=os.environ.get("FREELLMAPI_API_KEY", ""),
        type="password",
        help="The key starting with freellmapi-… from the Keys page. Not a provider key.",
    )
    base = normalise_base(base_url)

    demo = st.toggle(
        "Demo mode (no router needed)",
        value=False,
        help="Sample replies only, so you can look around before installing anything.",
    )

    col_a, col_b = st.columns(2)
    if col_a.button("Test connection", width="stretch", type="primary"):
        if demo:
            st.session_state.update(
                conn_error=None, models=DEMO_MODELS, connected=True, is_demo=True
            )
        else:
            with st.spinner("Knocking on the router…"):
                models, err = list_models(base, api_key)
            if err:
                st.session_state.update(conn_error=err, models=[], connected=False, is_demo=False)
            else:
                st.session_state.update(
                    conn_error=None, models=models, connected=True, is_demo=False
                )
    if col_b.button("Clear chat", width="stretch"):
        st.session_state["messages"] = []
        st.rerun()

    connected = st.session_state.get("connected", False)
    if demo:
        connected = True
        st.warning("**Demo mode is on.** Replies are samples — no AI is called and no key is used.")
    elif st.session_state.get("conn_error"):
        st.error("Not connected")
        st.markdown(st.session_state["conn_error"])
    elif connected:
        st.success(f"Connected — {len(st.session_state.get('models', []))} models available")
    else:
        st.info("Press **Test connection** after starting the router.")

    st.header("2. Pick a model")
    available = (DEMO_MODELS if demo else st.session_state.get("models")) or []
    choices = ["auto", "auto:fast", "auto:smart"] + (
        [m for m in available if m not in ("auto", "auto:fast", "auto:smart")]
    )
    model = st.selectbox(
        "Model",
        options=choices,
        index=0,
        help="`auto` is the safest choice — the router handles failover for you.",
    )
    if model in MODEL_HELP:
        st.caption(MODEL_HELP[model])

    temperature = st.slider("Creativity", 0.0, 1.5, 0.7, 0.1,
                            help="0 = focused and factual, 1+ = more varied")
    show_route = st.toggle("Show which provider answered", value=True)

    st.divider()
    st.caption(
        "Your key never leaves your laptop: this app calls your local router only. "
        "Full walkthrough in **GUIDE.md**."
    )

# ---------------- tabs ----------------
chat_tab, setup_tab, models_tab, help_tab = st.tabs(
    ["💬 Chat", "🚀 Setup (start here)", "📋 Available models", "🩺 Fix a problem"]
)

# ---- chat ----
with chat_tab:
    st.session_state.setdefault("messages", [])

    if not st.session_state["messages"]:
        if demo:
            st.info(
                "**Demo mode is on.** Type anything below to see how the chat behaves — the "
                "reply is a sample, not real AI. Turn demo mode off in the sidebar once your "
                "router is running to get real answers."
            )
        elif not connected:
            st.info(
                "**Welcome!** Two things first: start FreeLLMAPI on your laptop, then paste "
                "your unified key in the sidebar and press **Test connection**. "
                "The **Setup (start here)** tab has the whole thing in 5 steps. "
                "In a hurry? Flip on **Demo mode** in the sidebar to look around first."
            )
            st.markdown("**Quick start**")
            c1, c2, c3 = st.columns(3)
            c1.markdown(
                "**1 · Start the router**\n\nInstall the desktop app from the "
                "[Releases page](https://github.com/tashfeenahmed/freellmapi/releases/latest), "
                "or run the Docker one-liner. Leave it running."
            )
            c2.markdown(
                "**2 · Add one free key**\n\nIn the dashboard → **Keys**, paste a free "
                "Google AI Studio or Groq key. No credit card needed."
            )
            c3.markdown(
                "**3 · Come back here**\n\nCopy the `freellmapi-…` key from the Keys page, "
                "paste it in the sidebar, press **Test connection**."
            )
        else:
            st.markdown("#### Ready when you are")
            st.caption("Ask anything — normal questions, writing help, code, translation, summaries.")

        starters = [
            "Explain what FreeLLMAPI does like I'm not technical",
            "Write a polite email asking my landlord to fix the water heater",
            "Summarise the difference between HTTP 401 and 429 errors",
            "Turn these notes into a 3-line LinkedIn post: launched a side project, learned Python, 100 users",
        ]
        cols = st.columns(2)
        for i, s in enumerate(starters):
            if cols[i % 2].button(s, key=f"starter_{i}", width="stretch"):
                st.session_state["pending_prompt"] = s
                st.rerun()

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🆓"):
            st.markdown(msg["content"])
            if show_route and msg.get("route"):
                st.markdown(
                    f"<span class='route-chip'>answered by {msg['route']}</span>",
                    unsafe_allow_html=True,
                )

    prompt = st.chat_input("Type your message…")
    if st.session_state.get("pending_prompt"):
        prompt = st.session_state.pop("pending_prompt")

    if prompt:
        if not demo and not api_key.strip():
            st.warning("Add your unified `freellmapi-…` key in the sidebar first (step 1).")
        else:
            st.session_state["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="🧑"):
                st.markdown(prompt)
            with st.chat_message("assistant", avatar="🆓"):
                placeholder = st.empty()
                text, routed, error = "", None, None
                try:
                    with st.spinner("Demo reply…" if demo else "Routing to a free model…"):
                        if demo:
                            for word in DEMO_REPLY.split(" "):
                                text += word + " "
                                placeholder.markdown(text + "▌")
                            routed = "demo/sample"
                        else:
                            gen = stream_chat(
                                base,
                                api_key.strip(),
                                model,
                                [
                                    {"role": m["role"], "content": m["content"]}
                                    for m in st.session_state["messages"]
                                ],
                                temperature,
                            )
                            first_meta = next(gen)
                            routed = first_meta[1]
                            placeholder.markdown("▌")
                            for kind, value in gen:
                                if kind == "text":
                                    text += value
                                    placeholder.markdown(text + "▌")
                except RuntimeError as exc:
                    error = str(exc)
                placeholder.markdown(text if text else "")
                if error:
                    st.error(error)
                    # Drop the orphaned user turn so the next try starts clean
                    st.session_state["messages"].pop()
                    if "router isn't answering" in error:
                        st.info("Open the **Setup (start here)** tab — it walks through starting the router.")
                else:
                    st.session_state["messages"].append(
                        {"role": "assistant", "content": text or "_(empty reply)_", "route": routed}
                    )
                    if show_route and routed:
                        st.markdown(
                            f"<span class='route-chip'>answered by {routed}</span>",
                            unsafe_allow_html=True,
                        )

# ---- setup ----
with setup_tab:
    st.markdown(SETUP_STEPS)
    st.divider()
    st.markdown("#### Then point anything else at it")
    st.markdown(
        "FreeLLMAPI speaks the same language as OpenAI, so any app that asks for an "
        "“OpenAI API key” will accept your router:"
    )
    st.code(
        "Base URL:  http://localhost:3001/v1     (desktop app: http://127.0.0.1:31415/v1)\n"
        "API key:   freellmapi-… (your unified key)\n"
        "Model:     auto",
        language="text",
    )
    st.caption(
        "Test it in a terminal any time:  "
        '`curl http://localhost:3001/v1/models -H "Authorization: Bearer freellmapi-…"`'
    )
    with st.expander("Why is the free stuff free — and what are the catches?"):
        st.markdown(
            """
- Each provider gives away a small monthly allowance. Stacked together that adds up to
  billions of tokens — the router spreads your requests across them so you stop hitting limits.
- Free tiers are for **personal experimentation**. Don't build a paid product on them.
- Providers change limits and retire models without notice; the router updates its catalog
  on its own, so you don't have to chase changes.
- Your provider keys are encrypted on your own machine. Keep the `freellmapi-…` key private —
  anyone on your network who has it can spend your quota. Don't expose the router to the internet.
            """
        )

# ---- models ----
with models_tab:
    st.markdown("#### What your router can call right now")
    if not st.session_state.get("models"):
        st.info("Press **Test connection** in the sidebar to load the list.")
    else:
        query = st.text_input("Filter (e.g. llama, gemini, qwen)", "")
        rows = [m for m in st.session_state["models"] if query.lower() in m.lower()]
        st.caption(f"{len(rows)} of {len(st.session_state['models'])} models shown")
        st.dataframe({"model id": rows}, width="stretch", height=420)
        st.caption(
            "Tip: leave the sidebar on **auto** and let the router choose. Pin a model only "
            "when you need a specific one."
        )

# ---- help ----
with help_tab:
    st.markdown("#### The five things that usually go wrong")
    for title, body in TROUBLE:
        with st.expander(title, expanded=False):
            st.markdown(body)
    st.divider()
    st.markdown(
        """
**Still stuck?** In order, check:

1. Is the FreeLLMAPI app (or Docker container) actually running? Look for its icon in the
   tray / menu bar, or run `docker ps`.
2. Does the address in the sidebar match the port it uses — `31415` for the desktop app,
   `3001` for Docker?
3. Is the key the `freellmapi-…` one, not a provider key like `gsk_…` or `AIza…`?
4. Does the dashboard itself work? If the dashboard can't chat either, the problem is the
   router/provider keys, not this app.
5. Still nothing: restart the router. Your keys and history are saved, nothing is lost.
        """
    )
