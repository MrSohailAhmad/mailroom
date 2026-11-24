# Mailroom

A command-line tool for one newsletter, Kettlebird Tea's Steep Club. It reads the subscribers, checks an issue against the rules, and sends it to a **practice** mail server on your own computer. Every subscriber is made up (`@example.com`), and sending works only against `localhost`.

## Run it

```bash
uv sync
uv run mailroom --help
uv run mailroom subscribers --since-days 30 --run-date 2026-11-20
uv run mailroom next-send --run-date 2026-11-20
uv run mailroom check issues/issue-01.md
uv run mailroom import data/new-signups.csv --run-date 2026-11-20
uv run mailroom send issues/issue-01.md --dry-run --run-date 2026-12-07
```

Sending needs the practice server in a second terminal:

```bash
npx emulate@0.12.3 start --service resend
uv run mailroom send-one issues/issue-01.md --to delivered@resend.dev
uv run mailroom send issues/issue-01.md --run-date 2026-12-07 --latency 0.3 --at-once 5
```

## Checks

```bash
uv run pytest
uv run pyright
```

Rules for working on this project are in [AGENTS.md](AGENTS.md). My predictions for each step are in [notes/predictions.md](notes/predictions.md).
