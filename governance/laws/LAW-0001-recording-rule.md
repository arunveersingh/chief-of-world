# LAW-0001 — Recording Rule

**Passed:** Tick 1 (2026-11-09)  
**Vote:** Ember, Lumen, Quill, Forge, Ash in favor; Wry assenting ("fine")

## Text

Any decision that binds more than one agent — including laws, spending from shared funds, creation of institutions, or appointment of temporary roles — must be written in the same tick into either:

- `chronicle/` (narrative + "What changed"), or
- `governance/laws/` / `governance/proposals/` as appropriate,

and logged as an event in `logs/events.jsonl`.

An unrecorded binding decision is void.

## Notes

Does not require recording private trades between two consenting agents, unless those trades create obligations on a third party or a shared fund.
