# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## QUINN Context Database (USB)

**Location:** `/Volumes/QUINN/` (32GB exFAT USB3.1)

### Folder Structure
```
context/           # Session context data
├── sessions/      # Chat/agent session logs
├── embeddings/    # Vector embeddings cache
└── vectors/       # FAISS/pinecone vector indices

memory/            # Memory hierarchy
├── daily/         # Daily session logs (YYYY-MM-DD.md)
├── weekly/        # Weekly summaries
└── monthly/       # Monthly consolidations

knowledge/         # Structured knowledge base
├── facts/         # Discovered facts about user/environment
├── patterns/      # Recognized patterns
├── rules/         # Operational rules/preferences
└── skills/       # Skill documentation & configs

cache/             # Temporary cache
├── temp/          # Short-term temporary files
└── processed/     # Processed data awaiting storage

backups/           # Backup snapshots
```

### Usage
- Daily memory logs → `memory/daily/YYYY-MM-DD.md`
- Session context → `context/sessions/`
- Vector embeddings → `context/embeddings/`
- Knowledge base → `knowledge/{facts,patterns,rules,skills}/`

---

Add whatever helps you do your job. This is your cheat sheet.

## Pocket Option Bot - Chrome CDP Setup

### Chrome Launch Command
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --remote-debugging-address=0.0.0.0
```

### CDP Connection Settings
- Host: `127.0.0.1`
- Port: `9222`
- WebSocket: `ws://127.0.0.1:9222/devtools/browser/<id>`
- Timeout: 30s
- Auto-reconnect: enabled

### Bot Location
`/Users/ghost_mini/.openclaw/workspace/pocket-option-bot/`

### Trading Configuration
- Timeframe: 5-second to 1-minute expiry (scalping)
- Strategy: Combined Confluence (RSI + MACD + Price Action)
- Risk: 1-2% per trade max, daily loss limit enabled
- Mode: Paper trade first, then live

### Dependencies
- Python 3.9+
- aiohttp, websockets, websocket-client, requests
- pandas-ta (technical indicators)
- opencv-python (chart pattern matching)

### Quick Commands
```bash
cd pocket-option-bot
./setup.sh                    # Install deps + verify CDP
python main.py --analysis-only  # Test chart reading
python main.py --paper-trade    # Run without real money
python main.py --live --strategy combined  # Go live
```
