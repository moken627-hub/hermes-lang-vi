# hermes-lang-vi

Vietnamese (Tiếng Việt) language pack for Hermes Agent — core (CLI, gateway,
approval prompts, tips) + TUI + Desktop surfaces. Built 01/10/2026 following
the official language-pack spec (docs/user-guide/features/language-packs.md).

- `locales/vi.yaml` — 3,434 keys translated from `locales/en.yaml` (core surface)
- `locales/vi.tui.yaml` — 1,244 keys (TUI surface, phase 2)
- `locales/vi.desktop.yaml` — 4,922 keys (Desktop surface, phase 2)

Install: copy to `~/.hermes/plugins/hermes-lang-vi/`, enable in
`plugins.enabled`, then `hermes config set display.language vi` and restart
the gateway.

QA: placeholder parity, whitespace parity, parser-critical verbatim menus,
diacritics check — see `/root/5ac/research/hermes-lang-vi/plan.md`.
