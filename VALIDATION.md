# Validation — hermes-lang-vi

Recorded output of `hermes plugins validate` for the pinned release.

```text
✓ manifest — plugin.yaml parses
✓ manifest fields — name, version, description present
✓ requires_hermes — not declared
✓ config schema — not declared
✓ requires_env — all entries UPPER_SNAKE
✓ loadable — entry: __init__.py, locales/ (language pack)
✓ python dependencies — none declared
✓ capability probe — register() ran in isolation
✓ declared tools — matches registrations
✓ declared hooks — matches registrations
✓ declared middleware — matches registrations
✓ built-in tool collisions — no tools to check
✓ security scan — caution
✓ locale vi.desktop — vi.desktop.yaml: 4922 key(s), 4922 match the English 
desktop catalog
✓ locale vi.tui — vi.tui.yaml: 1244 key(s), 1244 match the English tui catalog
✓ locale vi — vi.yaml: 3434 key(s), 3434 match the English core catalog
⚠ security scan caution: agent_config_mod (vi.yaml:531), curl_pipe_shell 
(en_desktop_pairs.json:1616), curl_pipe_shell (vi.desktop.yaml:3172), 
ssh_dir_access (en_desktop_pairs.json:1593), ssh_dir_access 
(en_desktop_pairs.json:1596), ssh_dir_access (en_desktop_pairs.json:1599), 
ssh_dir_access (en_desktop_pairs.json:1600), ssh_dir_access 
(en_desktop_pairs.json:1602), ssh_dir_access (en_desktop_pairs.json:1604), 
ssh_dir_access (en_desktop_pairs.json:1614), sudo_usage 
(en_desktop_pairs.json:4771), sudo_usage (en_desktop_pairs.json:4774), 
sudo_usage (en_desktop_pairs.json:4776), sudo_usage 
(en_desktop_pairs.json:4777), sudo_usage (en_tui_pairs.json:492), sudo_usage 
(en_tui_pairs.json:515), sudo_usage (en_tui_pairs.json:545), sudo_usage 
(en_tui_pairs.json:889)

Validation passed.
```
