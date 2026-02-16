# .memory — Project Knowledge Base

> **⚠️ IMPORTANT: The root `AGENTS.md` file is the MASTER GUIDE for this repository.**
> **Agents and Developers:** Read `AGENTS.md` first. It consolidates build commands, style guides, and workflows.
> Use this `.memory/` folder for specific, deep-dive architectural details.

## Contents

| File | Purpose |
|------|---------|
| [../AGENTS.md](../AGENTS.md) | **MASTER GUIDE**: Build commands, style rules, workflows (Start Here) |
| [architecture.md](architecture.md) | Project structure, data flow, design patterns |
| [parser-guide.md](parser-guide.md) | How to add/modify parsers, shared utilities reference |
| [nmea-checksum.md](nmea-checksum.md) | Checksum mechanics, `fix_tests.py`, common pitfalls |
| [testing-guide.md](testing-guide.md) | Running tests, writing tests, coverage targets |
| [changelog.md](changelog.md) | History of significant refactors and decisions |

## Quick Start

Refer to `AGENTS.md` for the authoritative build and test commands.

## Rules

1. **Follow `AGENTS.md`** — It supercedes these docs if there is a conflict regarding style or commands.
2. **Read before coding** — Check the relevant guide before touching parser or test code.
3. **Run quality checks** — Always run `scripts\check_quality.bat` before committing.
4. **Update after changes** — If you change architecture or add parsers, update these docs.
5. **Use `fix_tests.py`** — After editing NMEA test data, run it to fix checksums.
6. **No `*XX` in tests** — Never use placeholder checksums; compute correct ones or omit entirely.
