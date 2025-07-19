
# Inbox Cleaner

> A cyberpunk-themed GUI tool to **clean up your Gmail inbox**, block annoying senders, and unsubscribe from marketing hell.

![](https://img.shields.io/badge/status-active-brightgreen)
![](https://img.shields.io/badge/built%20with-Tkinter%20+%20Gmail%20API-purple)
![](https://img.shields.io/badge/made%20for-zero%20bullshit%20email%20management-ff69b4)

---

## Why I Built This Tool

I'm gonna be honest, my inbox is a mess.

* I didn’t sign up for 90% of the crap I'm receiving.
* The “Unsubscribe” button in Gmail is buried and slow as fuck to get shit done.
* Most so-called "email cleaning tools" are:

  * **Paywalled**
  * Built for corporate newsletters, not everyday chaos
  * Lacking context or transparency (what's being deleted? what’s blocked?)
  * More interested in selling you upgrades than actually cleaning your inbox

They don’t **show you what’s happening** and they often just archive your emails instead of blocking or actually unsubscribing which happened to me. That’s not cleaning.

---

## What Makes Inbox Cleaner Different

**Inbox Cleaner** is built by someone who was sick to death of that.

* You can **see every sender**, subject, and unsubscribe link before taking action.
* You can **block** senders permanently with one click.
* You can **unsubscribe** from annoying emails instantly, even from multiple at once.
* The interface is a **fast, no-nonsense GUI**
* All logic is **local and transparent**
* It remembers what you've unsubscribed from to prevent repetition and wasted clicks.
* And it’s completely **free and open source.**

This is the email cleaner **I wish Gmail shipped by default**.

---

## Features

- Gmail API OAuth2 Authentication
- List all messages with `List-Unsubscribe` headers
- Smart parsing of unsubscribe links (HTTP and mailto)
- Add Gmail block filters on the fly
- Cyberpunk-themed GUI with slick fonts and colors
- Keeps track of previous blocks/unsubs so they don’t reappear

---

## Preview

```

CyberInbox Cleaner GUI
┌──────────────────────────────┬──────────────────────────────────────┬────────────────────────────────────────────┐
│          Brand               │               Subject                │             Unsubscribe Link               │
├──────────────────────────────┼──────────────────────────────────────┼────────────────────────────────────────────┤
│    [newsletter@annoying.com](mailto:newsletter@annoying.com)   │ "🔥🔥🔥 Hottest Deals Just for YOU!"  │ [http://unsubscribe.bait.click](http://unsubscribe.bait.click)           │
└──────────────────────────────┴──────────────────────────────────────┴────────────────────────────────────────────┘

\[📨 Unsubscribe Selected]   \[🚫 Block Selected]

````

---

## 🛠️ Installation

### 1. Clone the Repo

```bash
git clone https://github.com/Dyst0rti0n/inbox-cleaner.git
cd inbox-cleaner
````

### 2. Set Up a Google Cloud Project

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **Gmail API**
4. Go to **OAuth Consent Screen**, set user type to *External*, fill it out (name, email)
5. Go to **Credentials** → "Create Credentials" → *OAuth Client ID*

   * App Type: **Desktop App**
6. Download the `credentials.json` file and place it in the project root

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

> Requirements include:
>
> * `google-auth-oauthlib`
> * `google-api-python-client`
> * `tkinter`
> * `requests`

### 4. Usage

```bash
python email_cleaner_gui.py
```

When prompted, your browser will open, login and authorize access to Gmail.
It’ll create a `token.json` file for future runs (you’ll only need to auth once unless it expires).


---

## Common Issues

| Problem                       | Fix                                                                                                                |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `403 insufficientPermissions` | Ensure you’ve enabled Gmail API and used correct OAuth scopes                                                      |
| Emails keep reappearing       | You didn’t block the sender — just deleting doesn’t stop them                                                      |
| App won’t run                 | Ensure you have Python 3.8+ and all dependencies installed                                                         |
| Nothing shows in UI           | Your inbox may not contain any `List-Unsubscribe` headers — try searching manually in Gmail with `has:unsubscribe` |

---

## File Structure

```plaintext
.
├── email_cleaner_gui.py       # Main GUI
├── email_cleaner.py           # Gmail API interaction
├── credentials.json           # Your OAuth client file from Google
├── token.json                 # Generated token after login
├── requirements.txt
└── README.md
```

---

##  Roadmap

## Core Functionality (COMPLETED)

* [x] Authenticate with Gmail API using OAuth 2.0
* [x] Display a list of emails with `List-Unsubscribe` headers
* [x] Parse and extract unsubscribe links (HTTP + mailto)
* [x] Add "Unsubscribe" and "Block" functionality via Gmail filters
* [x] Build cyberpunk-themed Tkinter GUI
* [x] Smart deduplication of brands by sender address
* [x] Skip already-blocked or unsubscribed emails (via `get_blocked_addresses()` and `get_unsubscribed()`)

---

## QoLI (In Progress)

* [ ] Add "Refresh Inbox" button to reload subscriptions live
* [ ] Highlight already-unsubscribed senders visually
* [ ] Add search/filter bar to quickly find specific brands
* [ ] Save unsubscribed/blocked sender emails to local cache (e.g. JSON or SQLite)
* [ ] Confirmations in GUI for completed actions (e.g. "Unsubscribed from X")

---

## Automation

* [ ] Add headless unsubscribe automation for common link patterns
* [ ] Intelligent sender grouping (e.g. same domain, subdomains)
* [ ] AI-based subject line classifier (e.g. spam/promos/ads)
* [ ] Stats dashboard: how many senders unsubscribed/blocked over time
* [ ] Export unsubscribe/block reports as `.csv` or `.json`

---

## User & Dev Tools

* [ ] CLI version (`python email_cleaner.py --unsub --block --report`), unnecessary? Maybe just Linux support but who's wanting to be using this
* [ ] Build `.exe` binary using PyInstaller for easy Windows execution
* [ ] Add complete customisation through settings
* [ ] Add logging + error tracking system (e.g. log to `logs/errors.log`)
* [ ] Add support across most email providers

---

## Future

* [ ] Full dark mode toggle
* [ ] Multi-account selector
* [ ] Browser extension
* [ ] Plugin system (e.g. add new unsubscribe scrapers or visual themes)
* [ ] Gmail label management
* [ ] Add test harness using mock Gmail API responses

---

## Inspiration

* Gmail’s awful native "Unsubscribe" UX
* The cyberpunk aesthetic of tools like *Terminus* and *NeoMutt*
* The need to take back control of our digital lives | clean inbox = clean mind

---

## 🤝 Contributions

Want to help make it better? File issues or feature requests [here](https://github.com/Dyst0rti0n/inbox-cleaner/issues)
PRs welcome for anything in the roadmap or beyond.

---

## Credits

Built by [Dystortion](https://github.com/Dyst0rti0n)

---

## License

MIT — go wild
