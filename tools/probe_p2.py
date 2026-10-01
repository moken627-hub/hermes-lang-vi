"""Phase-2 probe — fresh process, INSTALLED pack, TUI + Desktop surfaces.

Gate for card t_a4f8bfea (deploy hermes-lang-vi v1.1.0). Runs the real plugin loader
(`PluginManager().discover_and_load()`) over the installed pack instead of registering the
locale files by hand, then asserts the *pack layer* serves Vietnamese for `tui` + `desktop`.

Evidence it produces:
  1. every pack registration the loader made for this pack (lang/surface/key-count/source/endonym)
  2. exact key counts for the three catalogs (core 3434 / tui 1244 / desktop 4922)
  3. two known keys (one TUI, one Desktop) resolved through `i18n.surface_catalog()` and compared
     against the English literal read out of the in-tree app sources — so "it is Vietnamese" is
     proven against EN, not against the pack itself
  4. proof the TUI/Desktop values can only come from the pack: no bundled `locales/vi.tui.yaml`
     or `locales/vi.desktop.yaml` exists in the Hermes tree
  5. endonym metadata ("Tiếng Việt", not "Vietnamese") as the language switcher would show it

Run (venv python so ruamel.yaml is importable):
  /usr/local/lib/hermes-agent/venv/bin/python3 \
      /root/5ac/scripts/infra/hermes-lang-vi/tools/probe_p2.py
Exit code 0 = all assertions passed.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, "/usr/local/lib/hermes-agent")

# The loader discovers plugins under $HERMES_HOME/plugins and honours $HERMES_HOME/config.yaml
# `plugins.enabled`. A Kanban worker shell exports HERMES_HOME=<profile dir>, whose plugins dir does
# NOT carry this pack — that run proves nothing about the live gateway. Pin the probe to the home the
# gateway actually runs with, and refuse to report a verdict otherwise.
HOME = Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes")).resolve()
PACK = HOME / "plugins" / "hermes-lang-vi"

if PACK.parent.parent != HOME.resolve() or HOME.name != ".hermes":
    print(f"PROBE MISCONFIGURED — HERMES_HOME={HOME} is not the pack's home "
          f"(expected .../.hermes). Re-run: HERMES_HOME=/root/.hermes "
          f"/usr/local/lib/hermes-agent/venv/bin/python3 {__file__}")
    sys.exit(2)
AGENT = Path("/usr/local/lib/hermes-agent")
LOCALES = PACK / "locales"

EXPECTED_KEYS = {"core": 3434, "tui": 1244, "desktop": 4922}

# (surface, key, EN source file in-tree, EN symbol name, expected VI value from the pack)
CASES = [
    ("tui", "billing.autoReload.aDifferentCard", AGENT / "ui-tui/src/i18n/en/billing.ts", "aDifferentCard"),
    ("desktop", "agents.activeCount", AGENT / "apps/desktop/src/i18n/en.ts", "activeCount"),
]

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)
    return ok


def en_literal(path: Path, symbol: str) -> str | None:
    """Pull the EN value of `symbol:` out of an in-tree TS i18n source (string or arrow fn)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(rf"{re.escape(symbol)}\s*:\s*(.+)$", text, re.M)
    return m.group(1).strip().rstrip(",") if m else None


print("=" * 78)
print("hermes-lang-vi Phase-2 probe — fresh process, installed pack")
print(f"HERMES_HOME: {HOME}")
print(f"pack: {PACK}")
print("=" * 78)

# ── 1. real loader sweep ────────────────────────────────────────────────────
from hermes_cli.plugins import PluginManager  # noqa: E402

pm = PluginManager()
pm.discover_and_load()

from agent import i18n, i18n_layers  # noqa: E402

print("\n-- pack registrations made by PluginManager.discover_and_load() --")
entries = [e for e in i18n_layers.registered_packs() if e.lang == "vi"]
if not entries:
    print("  (none)")
for e in entries:
    print(f"  lang={e.lang:<3} surface={e.surface:<8} keys={len(e.messages):<5} "
          f"endonym={e.endonym!r:<14} source={e.source}")
check("loader registered vi for all three surfaces",
      {e.surface for e in entries} == set(i18n_layers.SURFACES),
      f"surfaces={sorted(e.surface for e in entries)} vs expected={sorted(i18n_layers.SURFACES)}")

# ── 2. the pack layer itself (not overlay, not bundled) ─────────────────────
print("\n-- pack layer key counts (i18n_layers.pack_layer) --")
for surface, want in (("core", EXPECTED_KEYS["core"]), ("tui", EXPECTED_KEYS["tui"]),
                      ("desktop", EXPECTED_KEYS["desktop"])):
    got = len(i18n_layers.pack_layer("vi", surface))
    check(f"pack_layer vi/{surface} = {want} keys", got == want, f"got {got}")

print("\n-- serving layer (i18n.surface_catalog: packs > overlay > bundled) --")
catalogs = {s: i18n.surface_catalog("vi", s) for s in ("core", "tui", "desktop")}
for surface in ("core", "tui", "desktop"):
    got = len(catalogs[surface])
    check(f"surface_catalog vi/{surface} = {EXPECTED_KEYS[surface]} keys",
          got == EXPECTED_KEYS[surface], f"got {got}")

# ── 3. no bundled vi.<surface>.yaml -> those values can only come from the pack ──
print("\n-- provenance: bundled vi.<surface>.yaml in the Hermes tree? --")
for surface in ("tui", "desktop"):
    bundled = AGENT / "locales" / f"vi.{surface}.yaml"
    check(f"no bundled {bundled.name} (so surface_catalog vi/{surface} is pack-only)",
          not bundled.exists(), str(bundled))

check("locale files present in installed pack",
      all((LOCALES / f"vi{s}.yaml").is_file() for s in ("", ".tui", ".desktop")),
      ", ".join(sorted(p.name for p in LOCALES.glob("vi*.yaml"))))

# ── 4. known keys: resolved value must be VI and must differ from the EN literal ──
print("\n-- key lookups (value vs English source) --")
for surface, key, en_file, symbol in CASES:
    vi = catalogs[surface].get(key)
    en = en_literal(en_file, symbol)
    print(f"  {surface}/{key}\n    vi={vi!r}\n    en={en!r}  (from {en_file.name})")
    check(f"{surface}/{key} present in {surface} catalog", bool(vi), repr(vi))
    if vi:
        check(f"{surface}/{key} is non-ASCII Vietnamese", any(ord(c) > 127 for c in vi), repr(vi))
        if en:
            # EN for activeCount is an arrow fn `count => \`${count} active\`` — compare on the tail word.
            en_word = re.sub(r"^[^`]*`|`$", "", en).replace("${count}", "").strip()
            check(f"{surface}/{key} differs from English", vi.strip() != en.strip() and vi.strip() != en_word,
                  f"vi={vi!r} en={en_word!r}")

# ── 5. switcher metadata ────────────────────────────────────────────────────
print("\n-- language switcher metadata --")
info = i18n_layers.pack_info("vi")
print(f"  pack_info('vi') = {info}")
check("endonym is 'Tiếng Việt'", (info or {}).get("endonym") == "Tiếng Việt", repr((info or {}).get("endonym")))
opts = [o for o in i18n.language_options() if o.get("id") == "vi"]
print(f"  language_options vi = {opts}")
check("vi listed in language_options", bool(opts))
check("vi in supported_languages()", "vi" in i18n.supported_languages())
check("resolve_language_id('vi') == vi", i18n.resolve_language_id("vi") == "vi",
      repr(i18n.resolve_language_id("vi")))

print("\n" + "=" * 78)
if failures:
    print(f"PROBE FAILED — {len(failures)} check(s): {failures}")
    sys.exit(1)
print("PROBE PASSED — vi served from the pack on core + tui + desktop")
sys.exit(0)
