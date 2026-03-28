# Walter (Sage)

A Victorian-humour Discord bot written in [Sage](https://github.com/sagelang/sage). Posts daily "On This Day in History" briefings with rotating Victorian prose styles, plus water and electricity outage alerts for Sofia, Bulgaria.

This is a port of [Walter](https://github.com/cargopete/walter) from Python to Sage. See [RFC-0022](https://github.com/sagelang/rfcs/blob/main/rfcs/RFC-0022-walter-in-sage.md) for the full design rationale.

## Features

- Daily historical briefings from the Wikipedia "On This Day" API
- Victorian commentary in three rotating styles (standard, Pooter, Jerome)
- Sofia water supply interruption alerts (scraped via LLM extraction)
- Sofia electricity outage alerts (scraped via LLM extraction)
- Parallel data fetching with `summon`/`await`
- Discord webhook posting
- Supervision tree with `OneForOne` restart strategy

## Architecture

```
WalterSupervisor (OneForOne)
└── WalterBot
    └── DailyBriefingAgent (spawned per post)
        ├── HistoryAgent          — Wikipedia API + LLM selection
        ├── WaterStopsAgent       — HTML scrape + LLM extraction
        ├── ElectricityStopsAgent — HTML scrape + LLM extraction
        ├── CommentaryAgent       — Victorian prose generation
        └── DiscordAgent × 3      — Webhook posts (history, water, electricity)
```

Written in ~280 lines of Sage with ~200 lines of Rust extern functions for date/time handling, environment access, and string utilities.

## Usage

```bash
# Install Sage
brew install sagelang/sage/sage

# Configure
export SAGE_API_KEY="your-openai-api-key"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Run in scheduler mode (posts daily at 10:10 UTC)
sage run .

# Or fire one briefing immediately
WALTER_TRIGGER=1 sage run .
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_WEBHOOK_URL` | Discord webhook URL (required) | — |
| `SAGE_API_KEY` | API key for LLM provider | — |
| `POST_HOUR` | Hour (UTC) to post daily briefing | `10` |
| `POST_MINUTE` | Minute to post daily briefing | `10` |

## Sage Features Demonstrated

- **Agents** as first-class primitives with typed state
- **summon/await** for parallel data fetching
- **divine** for LLM-powered text generation and HTML extraction
- **Http tool** for Wikipedia API and web scraping
- **Supervision trees** with `OneForOne` restart strategy
- **Extern functions** (Rust FFI) for date/time and string utilities
- **try/catch** error handling with graceful fallbacks

## Related

- [sagelang/sage](https://github.com/sagelang/sage) — The Sage programming language
- [sagelang/rfcs](https://github.com/sagelang/rfcs) — Language design RFCs
- [RFC-0022](https://github.com/sagelang/rfcs/blob/main/rfcs/RFC-0022-walter-in-sage.md) — Walter design document
- [cargopete/walter](https://github.com/cargopete/walter) — Original Python implementation

## License

MIT
