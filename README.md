# hermes-lang-vi

**Vietnamese language pack for [Hermes Agent](https://github.com/NousResearch/hermes-agent)** — full UI translation across every surface: gateway, CLI, TUI, Desktop, approval prompts, tips, slash-command descriptions.

**9,600 keys** — built on the official language-pack plugin spec announced by Teknium (Oct 2026): core `vi.yaml` (3,434) + `vi.tui.yaml` (1,244) + `vi.desktop.yaml` (4,922).

## Install

```bash
# Copy the pack into your Hermes plugins directory
git clone https://github.com/moken627-hub/hermes-lang-vi.git
mkdir -p ~/.hermes/plugins
cp -r hermes-lang-vi ~/.hermes/plugins/

# Enable it
hermes config set plugins.enabled '["hermes-lang-vi", ...existing...]'
hermes config set display.language vi

# Restart the gateway (from outside any Hermes session)
systemctl --user try-restart hermes-gateway.service
```

Validate:

```bash
hermes plugins validate ~/.hermes/plugins/hermes-lang-vi
# locale vi — vi.yaml: 3434 key(s) ...
# locale vi.tui — vi.tui.yaml: 1244 key(s) ...
# locale vi.desktop — vi.desktop.yaml: 4922 key(s) ...
# Validation passed.
```

## Parser-safe translation

Menu brackets, token lists and confirmation prompts that Hermes parses byte-exact are kept verbatim:

- Approval menus `[o]nce | [s]ession | [D]eny` stay in English (hard-parsed)
- `pm/extras.py` first-run `[Y/n]` stays verbatim (hard-parsed `{"y","yes"}`)
- `cli.shared.yes_initial`/`no_initial` are localized (`c`/`k`) — `cli_output.py` accepts the localized initial natively
- Placeholders `{name}`, `{0}`, `{1}`, literal `\n`, URLs, CLI flags: 100% preserved (validated 3,434+1,244+4,922 vs EN catalogs)

## Quality gates

Every key passed: placeholder parity, whitespace parity, verbatim-token parity, menu-bracket safety, Vietnamese diacritics check (with loanword whitelist), faithful-empty check (keys empty in EN stay empty in VI). Cross-model review: translation lane ≠ review lane.

## Compatibility

- Hermes Agent with language-pack plugin support (spec Oct 2026)
- Locale resolution: pack > overlay > bundled > en (safe fallback to English)

## About

**hermes-lang-vi** is built and maintained by [5ac](https://5ac.vn) — an Agentic AI consultancy from Vietnam and the maker of **G-Company OS**, an AI agent platform for SMB sales, marketing, finance and operations.

- 🌐 Website: [5ac.vn](https://5ac.vn)
- 🧩 More Hermes plugins from us: [hermes-plugin-zalo](https://github.com/moken627-hub/hermes-plugin-zalo) — Zalo messaging platform plugin for Hermes Agent (production-tested)

The translation itself is contributed to the Hermes community under MIT. If your business needs AI agents that work in Vietnamese end-to-end, that's literally what we do.

## License

MIT — Vietnamese translation © 2026 5ac. Hermes Agent UI strings © Nous Research (MIT).
