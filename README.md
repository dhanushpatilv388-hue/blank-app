# 🆓 FreeLLMAPI Chat

A friendly chat window for a [FreeLLMAPI](https://github.com/tashfeenahmed/freellmapi) router
running on your own laptop: one free-tier key pool, one endpoint, automatic failover.

**[👉 Start here: GUIDE.md](GUIDE.md)** — plain-English setup for people with no coding
background (which download to click, where to get free keys, what to do when it breaks).

## What's here

| File | What it is |
|---|---|
| `GUIDE.md` | The step-by-step walkthrough. Read this first. |
| `streamlit_app.py` | The chat app: connect to your router, pick a model, chat, see which provider answered. |
| `requirements.txt` | The two Python packages the app needs. |

## Run it

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

No router yet? Flip on **Demo mode** in the sidebar to see the app with sample replies.

Then in the sidebar pick where your router is running — desktop app uses
`http://127.0.0.1:31415/v1`, Docker uses `http://localhost:3001/v1` — and paste the
unified `freellmapi-…` key from the dashboard's **Keys** page. Press **Test connection**.

## Notes

- The app only ever talks to your local router. Nothing is uploaded, and the key is held in
  the browser tab's memory, not written to disk.
- It must run on the same machine as FreeLLMAPI (`localhost` means "this laptop"), so hosting
  it online will not work.
- Free tiers are for personal experimentation — see the guide's safety section.
