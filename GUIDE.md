# How to use FreeLLMAPI from your laptop

**Written for people who don't code.** No jargon assumed — every technical word is
explained in [the glossary](#glossary) at the bottom. Take it one step at a time;
you can stop after Step 3 and already be chatting.

---

## What is FreeLLMAPI, really?

Big AI companies (Google, Groq, Mistral, and about thirty more) each give away a small
**free** amount of AI usage every month. Individually that's a toy. Together it's billions
of words' worth.

The catch: each company has its own website, its own key, its own limits. So people
give up and pay.

**FreeLLMAPI is a small program you run on your own laptop.** You paste your free keys
into it once. It then gives you *one* address and *one* password that every AI app can
use, and it quietly switches to whichever company still has free quota left.

Think of it as a **power strip** for free AI: one plug for you, many sockets behind it,
and it flips to a live socket when one goes dead.

```
Your app  ──►  FreeLLMAPI (on your laptop)  ──►  Google / Groq / Mistral / … free tiers
              one address, one key, automatic failover
```

### Will this give me Claude or ChatGPT for free?

**No.** Say it plainly, because it's the most common misunderstanding:

- Anthropic (Claude) and OpenAI (ChatGPT) do **not** offer a free API tier. Their free
  chatbots are websites — they can't be plugged into this.
- FreeLLMAPI's "Claude support" means something different: it *speaks Claude's language*
  so tools built for Claude (like the Claude Code command-line tool) can run on it. When
  such a tool asks for `claude-sonnet-4-5`, the router quietly answers with a **free open
  model** (Qwen, GLM, Kimi, Llama, DeepSeek…). You get the tool, not the Claude brain.
- What you actually get free: very good open-weight models — Qwen3 235B, GLM-5, Kimi,
  DeepSeek, Llama, GPT-OSS 120B — from Google, Groq, Cerebras and friends. For summaries,
  writing, translation, everyday code and Q&A they're genuinely close. For the hardest
  reasoning they fall short of paid Claude/GPT-5-class models.
- The project's own docs admit the limits: "no frontier models, variable latency, no SLA."
  If a task must be the absolute best, use a paid model for that one task.

Two honest notes before you start:

- This is for **personal use** — experiments, learning, small side projects. Don't build a
  business on free tiers; they can change or vanish.
- Free models are sometimes slow because everyone else is also using the free tier.
  That's normal. The router handles it; you just wait a few seconds.

---

## What you need

| Thing | Details |
|---|---|
| A laptop | Windows 10/11 or macOS 12+. Linux works too. |
| Internet | Obviously. |
| Free accounts | At least **one** provider key (Step 2). Two is better. |
| Money | ₹0. No credit card is required for the providers linked below. |
| Coding | None. You will copy-paste, not write. |

You do **not** need an account on freellmapi.co, and you don't need to pay the $19/year
"premium" option. That only makes the model catalogue refresh faster. The free version is
fully functional.

---

## Step 1 — Install FreeLLMAPI on your laptop

Pick **one** of the two routes. Route A is the easy one.

### Route A — Desktop app (recommended if you don't code)

1. Open the downloads page:
   **<https://github.com/tashfeenahmed/freellmapi/releases/latest>**
2. On **Windows**, download the file ending in **`.exe`** (`FreeLLMAPI-Setup-….exe`) and
   double-click it. If Windows shows a blue "Windows protected your PC" box, click
   **More info → Run anyway**. That warning appears because the app is free and unsigned,
   not because anything is wrong with it.
3. On a **Mac**, download the **`.dmg`** — `arm64` if your Mac is Apple Silicon (M1/M2/M3/M4),
   `x64` if it's an older Intel Mac. Open it and drag the app into **Applications**.
   (Not sure which Mac you have?  → Apple menu  →  *About This Mac*  →  look at "Chip".)
4. Launch the app. It lives in your **system tray** (Windows: bottom-right, near the clock —
   you may need to click the `^` arrow) or your **menu bar** (Mac: top-right).
5. Click the tray icon → **Open Dashboard**.

The dashboard opens in your browser at **<http://127.0.0.1:31415>**. There is no password to
create — the desktop app signs itself in. Keep the tray app running whenever you want to use AI.

> If the tray menu shows a different port number (it moves if 31415 is busy), use that one.
> You'll need it later.

### Route B — Docker (one line, if you don't mind a terminal)

Only if you already have **Docker Desktop** installed and running. Otherwise use Route A —
installing Docker just for this is more work than the desktop app.

```bash
curl -fsSL https://freellmapi.co/install.sh | bash
```

Then open **<http://localhost:3001>** and create a dashboard account (email + password of
your choosing — it never leaves your laptop). Re-running the command later is safe; it just
updates the app and keeps your keys.

### Route C — Windows without installing anything

You can also run the Docker route inside WSL, or build from source with Node.js 20+:

```bash
git clone https://github.com/tashfeenahmed/freellmapi.git
cd freellmapi
npm install
npm run dev          # API + dashboard
```

This is the developer path. If that sentence felt uncomfortable, go back to Route A.

---

## Step 2 — Add one free provider key

A **key** is just a long password that proves to Google (or Groq, etc.) that the request
is yours. You generate it on the company's website in about 30 seconds.

Get two — one is enough to start, two makes the failover useful:

### Google AI Studio (usually the most tokens)

1. Go to **<https://aistudio.google.com/apikey>** and sign in with any Google account.
2. Click **Create API key** → choose/create a project if it asks.
3. Copy the string that starts with `AIza…`.

### Groq (very fast, good for quick answers)

1. Go to **<https://console.groq.com/keys>** and sign up (Google/GitHub login works).
2. Click **Create API Key**, name it anything (e.g. "laptop").
3. Copy the string that starts with `gsk_…` — it's shown **once**, so paste it somewhere safe
   for a minute.

*(Optional extras, same idea: Cerebras, Mistral, OpenRouter, NVIDIA, Cloudflare, Cohere.
The dashboard's Keys page lists every supported provider with a link to where its key lives.)*

### Put the keys into FreeLLMAPI

1. In the dashboard, click **Keys** in the left sidebar.
2. Pick the provider (e.g. Google), paste the key, press **Save**. It shows a green tick.
3. Repeat for the second provider.
4. Optional but useful: click **Test** next to each key to confirm it works.

Your keys are encrypted on your laptop. They are never sent anywhere except to the company
that issued them.

---

## Step 3 — Copy your one unified key

Still on the **Keys** page, look at the header area. There is a key that starts with
**`freellmapi-…`** with a copy button.

**This is the only key you will ever need again.** It represents all the others.
Treat it like a house key: don't post it publicly.

You now have everything required. Two ways to actually chat:

- Fastest check: the dashboard's own **Playground** page → type a message → it answers.
- Nicer interface: the app in this repo, explained next.

---

## Step 4 — Chat with the app in this repo (optional but nicer)

This repository contains a simple chat window (`streamlit_app.py`) that connects to your
router. It runs on your laptop too, so nothing is uploaded anywhere.

### One-time setup

You need Python 3.9+ (Windows: get it from <https://python.org>, tick **"Add Python to PATH"**
during install; Mac: it's often already there — check by typing `python3 -V`).

**Windows** — open **Command Prompt** (press `Win`, type `cmd`, Enter) and paste these lines
one at a time:

```bat
cd %USERPROFILE%\Downloads\blank-app
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

**Mac** — open **Terminal** (press `Cmd+Space`, type `Terminal`, Enter):

```bash
cd ~/Downloads/blank-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

*(Adjust the `cd` line to wherever you saved this folder.)*

Your browser opens at <http://localhost:8501>. From then on, to use it again you only need
the last two lines (`activate`, then `streamlit run streamlit_app.py`). Close the terminal
window to stop it.

Don't want to install anything yet? Flip on **Demo mode** in the app's sidebar — it shows
sample replies so you can see how the chat behaves. No key, no router, nothing sent anywhere.

### In the app

1. Sidebar → **Where is FreeLLMAPI running?**
   - Desktop app → pick *Desktop app (port 31415)*
   - Docker → pick *Docker / installer (port 3001)*
2. Paste the **`freellmapi-…`** key into **Unified API key**.
3. Press **Test connection**. You should see *"Connected — N models available"*.
4. Leave the model on **auto**, make sure **Demo mode is off**, and start typing.

Under each answer you'll see a small label — *answered by groq/llama-3.3-70b* — so you can
see which free provider served you. That's the router doing its job.

The app's own **Setup** and **Fix a problem** tabs repeat the essentials, so you can throw
this file away and still be fine.

---

## Step 5 — Use it from everything else

Because FreeLLMAPI speaks the same language as OpenAI, any app that has a box asking for an
"OpenAI API key" will accept your router. Look for settings called
**Base URL / API endpoint / Custom provider**, and fill in:

| Field | Value |
|---|---|
| Base URL | `http://localhost:3001/v1` — or `http://127.0.0.1:31415/v1` for the desktop app |
| API key | your `freellmapi-…` key |
| Model | `auto` (or a specific id from the Models page) |

That covers things like Obsidian AI plugins, Jan, LibreChat, Cursor/Cline (as a custom
OpenAI endpoint), n8n, and any script of your own. The router also offers
Anthropic-style and Gemini-style addresses for tools that expect those instead —
see the project's own docs if you get there.

If you ever want to test from a terminal, this proves the router is alive:

```bash
curl http://localhost:3001/v1/models -H "Authorization: Bearer freellmapi-YOURKEY"
```

A list of model names means everything is working.

---

## Everyday tips

- **Leave the model on `auto`.** It's the whole point — the router picks a model with quota
  and retries elsewhere on failure.
- `auto:fast` when you want speed, `auto:smart` when the question is hard,
  `fusion` when you want several models to answer and be merged (slower, usually better).
- **More keys = fewer waits.** When you see *"rate limited"*, adding one more free provider
  key usually fixes it permanently.
- **Models come and go.** Free plans change weekly. The router downloads an updated catalogue
  on its own; you don't have to reinstall anything.
- **Keep the app running.** Closing the tray app (or stopping Docker) means no AI for the
  other apps pointing at it.
- **Watch the quota page.** The dashboard shows how much of each free tier you've used today
  and this month, so you can see what's running out.

---

## Keep it safe

- **Never expose the router to the internet.** It's single-user and protected only by that
  one key. No port forwarding, no public tunnels. It's designed to listen on your own machine.
- If you ever share a laptop or suspect the key leaked, **regenerate the unified key** in the
  dashboard. Your provider keys stay put.
- Provider keys are encrypted at rest. Still, don't commit them to GitHub or paste them into
  chat apps.
- Free tiers are for experimentation. Reading provider terms once is worth five minutes —
  some forbid commercial use.

---

## Troubleshooting

| What you see | What it means | Fix |
|---|---|---|
| Browser can't open `127.0.0.1:31415` | Desktop app isn't running | Launch it; check the tray icon. If it shows a different port, use that. |
| Browser can't open `localhost:3001` | Docker isn't running | Open Docker Desktop, wait for the whale icon to settle, run `docker compose up -d` in the freellmapi folder. |
| App says *"router isn't answering"* | Same as above — the address/port is wrong or nothing is running | Check the sidebar choice: 31415 = desktop, 3001 = Docker. |
| `401 Unauthorized` | Wrong key | You pasted a provider key (`gsk_`, `AIza`) instead of `freellmapi-…`. |
| `404 Not found` | Wrong address | Base URL must end in `/v1`, and nothing more. |
| `429` / "rate limited" | All your free tiers are used up right now | Add another provider key, or wait for the reset (usually minutes to hours). |
| Model list is empty | Router running, no provider keys added | Add a key on the Keys page, press Test connection again. |
| Answers are very slow | Free tier congestion | Switch to `auto:fast`; try a smaller model. |
| Dashboard asks for a password (Docker install) | Normal for server installs | Use the account you created. Forgot it → **Forgot password?**, and the code appears in `docker compose logs -f freellmapi`. |
| Everything broke after an update | Rare | Quit and relaunch. Your keys and history are in a data folder; updates don't delete them. |

Where your data lives (useful if you want to back it up):

- Windows: `%APPDATA%\FreeLLMAPI\`
- macOS: `~/Library/Application Support/FreeLLMAPI/`
- Linux / Docker: `~/.config/FreeLLMAPI/` or the Docker volume

---

## Glossary

| Word | Plain meaning |
|---|---|
| **Provider** | A company that offers AI, e.g. Google, Groq, Mistral. |
| **API key** | A long password that identifies you to a provider. Generate it on their site. |
| **Unified key** | The `freellmapi-…` key. One key for all providers; it's what apps use. |
| **Base URL** | The address of the router, e.g. `http://localhost:3001/v1`. "localhost" = this laptop. |
| **Endpoint** | One specific door on that address, e.g. `/chat/completions` for chatting. |
| **Router** | FreeLLMAPI itself — it decides which provider gets each request. |
| **Failover** | When one provider says "no", automatically trying the next. |
| **Token** | Roughly ¾ of a word. Free tiers are counted in tokens per minute/day/month. |
| **Rate limit** | A provider's "you've had enough for now" (the `429` error). |
| **Streaming** | The answer appearing word by word instead of all at once. |
| **`auto`** | A model name that means "router, you choose". |

---

## Uninstall

1. Remove the app (Trash on Mac, *Settings → Apps* on Windows, or `docker compose down -v`).
2. Delete the data folder listed above.
3. Delete your provider keys on each provider's website if you want them dead for good.

Nothing else is left behind — there is no account with FreeLLMAPI to cancel.

---

*FreeLLMAPI is an open-source project by Tashfeen Ahmed (MIT licence), not affiliated with the
providers it routes to. Links: [repository](https://github.com/tashfeenahmed/freellmapi) ·
[model catalogue](https://freellmapi.co/models.html). This guide was written for this repo's
chat app and checked against the project's docs in October 2026 — if a menu has moved, the
project's own [install docs](https://github.com/tashfeenahmed/freellmapi/blob/main/docs/en/install/01-install.md)
are the authority.*
