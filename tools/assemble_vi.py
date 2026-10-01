"""QA + assemble Vietnamese language pack from translation chunk outputs.

Usage: python3 vi_pack_assemble.py
Reads out_*.tsv from scratch/vi_pack, validates against en_flat.txt,
builds plugin tree, writes vi.yaml.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, "/usr/local/lib/hermes-agent")

EN_FLAT = Path("/root/5ac/scripts/infra/hermes-lang-vi/tools/en_flat.txt")
CHUNK_DIR = Path("/root/5ac/scripts/infra/hermes-lang-vi/tools/vi_pack_workdir")
PACK_DIR = Path("/root/5ac/scripts/infra/hermes-lang-vi")
LOCALES = PACK_DIR / "locales"

CHUNKS = [
    ("cli_a", "out_cli_a.tsv"),
    ("cli_b", "out_cli_b.tsv"),
    ("gateway", "out_gateway.tsv"),
    ("platform_tips", "out_platform_tips.tsv"),
    ("display_slash", "out_display_slash.tsv"),
    ("approval_explainer", "out_approval_explainer.tsv"),
]

PH_RE = re.compile(r"\{[a-zA-Z0-9_]+\}|\{\d+\}")
BRACKET_CHOICE_KEYS_EXEMPT = ("cli.shared.yes_no_default_yes", "cli.shared.yes_no_default_no")


def has_vi_diacritics(s: str) -> bool:
    """True when the string carries Vietnamese diacritics (NFD marks or đ/ơ/ư)."""
    import unicodedata

    if any(c in "đĐơƠưƯ" for c in s):
        return True
    decomp = unicodedata.normalize("NFD", s)
    return bool(re.search(r"[\u0300-\u036f]", decomp))
ALLOWLIST_NO_DIACRITICS = {
    "", "-", "—", "/", "|", "OK", "OK, got it", "Hermes", "API", "CLI", "TUI",
    "Token", "token", "config", "hermes", "o", "d", "s", "a",
}


def load_tsv(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for i, ln in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not ln.strip():
            continue
        parts = ln.split("\t", 1)
        if len(parts) != 2:
            print(f"  WARN {path.name}:{i} not TSV: {ln[:60]!r}")
            continue
        rows[parts[0]] = parts[1]
    return rows


def main() -> None:
    en = {}
    for ln in EN_FLAT.read_text(encoding="utf-8").splitlines():
        k, _, v = ln.partition("\t")
        en[k] = v
    print(f"EN keys: {len(en)}")

    vi_all: dict[str, str] = {}
    errors: list[str] = []
    for name, outname in CHUNKS:
        path = CHUNK_DIR / outname
        if not path.is_file():
            errors.append(f"MISSING OUTPUT: {outname}")
            continue
        rows = load_tsv(path)
        print(f"{outname}: {len(rows)} rows")
        for k, v in rows.items():
            if k in vi_all:
                errors.append(f"DUP across chunks: {k}")
            vi_all[k] = v

    # Gate 1: key set match
    missing = set(en) - set(vi_all)
    extra = set(vi_all) - set(en)
    if missing:
        errors.append(f"MISSING {len(missing)} keys, e.g. {sorted(missing)[:5]}")
    if extra:
        errors.append(f"EXTRA {len(extra)} keys, e.g. {sorted(extra)[:5]}")

    # Gates 2-6 per key (only for keys present in both)
    ph_bad, ws_bad, verb_bad, dia_bad, txt_bad = [], [], [], [], []
    for k in sorted(set(en) & set(vi_all)):
        ev, vv = en[k], vi_all[k]
        if sorted(PH_RE.findall(ev)) != sorted(PH_RE.findall(vv)):
            ph_bad.append(k)
        # Whitespace gate: compare leading/trailing runs separately (content may differ).
        lead = re.match(r"\s*", ev).group(0)
        trail = re.search(r"\s*$", ev).group(0)
        if vv[: len(lead)] != lead or (trail and vv[-len(trail):] != trail):
            ws_bad.append(k)
        if k.startswith(("approval.", "explainer.")):
            ev_n = re.sub(r"\s+", " ", ev)
            vv_n = re.sub(r"\s+", " ", vv)
            has_menu = bool(re.search(r"\[[a-z]\]", ev)) or bool(re.search(r"\[[a-z]/", ev))
            token_list = "," in ev and all(len(w) <= 12 for w in ev.split(",") if w.strip())
            if (has_menu or token_list) and ev_n != vv_n:
                verb_bad.append(k)
        if not has_vi_diacritics(vv) and ev.strip() != vv.strip():
            dia_bad.append(k)
        if vv == "" or isinstance(vv, (int, float, bool)):
            txt_bad.append(k)

    # Gate 4b: bracket-choice prompts anywhere must keep their bracket letters
    # verbatim (approval parser + confirm prompts read the letters users type).
    # Surrounding prose may be translated. cli.shared.yes_* is EXCLUDED:
    # cli_output.py reads the localized yes_initial and accepts it natively
    # (startswith(("y", yes_initial))), so c/c/K is a valid localization.
    BRACKET_RE = re.compile(r"\[[A-Za-z]/[A-Za-z]\]|\[[a-z]\]")
    bracket_bad: list[str] = []
    for k in sorted(set(en) & set(vi_all)):
        ev, vv = en[k], vi_all[k]
        if BRACKET_RE.search(ev) and k not in ("cli.shared.yes_no_default_yes", "cli.shared.yes_no_default_no"):
            en_letters = re.findall(r"\[[A-Za-z](?:/[A-Za-z])?\]", ev)
            vi_letters = re.findall(r"\[[A-Za-z](?:/[A-Za-z])?\]", vv)
            if en_letters != vi_letters:
                bracket_bad.append(k)

    print("\n=== GATES ===")
    print(f"placeholder mismatches: {len(ph_bad)}")
    print(f"whitespace mismatches: {len(ws_bad)}")
    print(f"verbatim violations: {len(verb_bad)}")
    print(f"bracket-letter violations: {len(bracket_bad)}")
    print(f"no-diacritics suspects: {len(dia_bad)}")
    print(f"non-text values: {len(txt_bad)}")

    report_lines = []
    if ph_bad:
        report_lines.append("## Placeholder mismatch — revert về EN:\n" + "\n".join(ph_bad[:50]))
    if ws_bad:
        report_lines.append("## Whitespace mismatch (prefix/suffix khác EN):\n" + "\n".join(ws_bad[:80]))
    if verb_bad:
        report_lines.append("## Verbatim violation (approval menu/token list bị dịch):\n" + "\n".join(verb_bad[:50]))
    if bracket_bad:
        report_lines.append("## Bracket-letter violation ([Y/n] bị đổi chữ):\n" + "\n".join(bracket_bad[:50]))
    if dia_bad:
        report_lines.append(
            "## Suspect no-diacritics (KHÔNG auto-revert — reviewer đối chiếu: giữ nguyên chủ đích hay thiếu dấu):\n"
            + "\n".join(f"{k}\t{vi_all[k][:60]}" for k in dia_bad[:120])
        )
    kept_en = [k for k in sorted(set(en) & set(vi_all)) if vi_all[k] == en[k]]
    report_lines.append(f"## Kept verbatim EN: {len(kept_en)} keys (thuần placeholder/shortcut/thuật ngữ — hợp lệ)")

    fixable = ph_bad + ws_bad + verb_bad + bracket_bad
    for k in fixable:
        vi_all[k] = en[k]  # safe fallback: revert to EN string, runtime vẫn đúng
    if fixable:
        report_lines.append(f"## AUTO-REVERTED to EN: {len(fixable)} keys (xem list ở trên)")

    (CHUNK_DIR / "qa_report.md").write_text(
        ("# QA Report vi.yaml\n\n" + "\n\n".join(report_lines)) if report_lines else "# QA Report vi.yaml\n\nCLEAN — 0 issues.",
        encoding="utf-8",
    )

    if errors:
        print("\n=== BLOCKING ERRORS ===")
        for e in errors:
            print(" -", e)
        print("ABORT: not assembling.")
        return

    # Assemble nested vi.yaml preserving en.yaml structure
    import io as _io

    from ruamel.yaml import YAML as _YAML

    tree: dict = {}
    for k in sorted(en):
        if k not in vi_all:
            continue
        node = tree
        parts = k.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = vi_all[k]

    LOCALES.mkdir(parents=True, exist_ok=True)
    out_yaml = LOCALES / "vi.yaml"
    header = (
        "# Hermes Agent — Vietnamese (Tiếng Việt) language pack, core surface.\n"
        "# Generated 01/10/2026 from locales/en.yaml (3,433 keys). Placeholders preserved.\n"
    )
    y = _YAML()
    y.default_flow_style = False
    y.width = 4096
    y.representer.ignore_aliases = lambda *args: True  # noqa: ARG005
    buf = _io.StringIO()
    y.dump(tree, buf)
    out_yaml.write_text(header + buf.getvalue(), encoding="utf-8")

    # Fixup: YAML 1.1 parses bare OFF/ON/YES/NO/true/false/null as booleans/null,
    # which the validator (hermes_yaml.safe_load + non_text_leaves) rejects.
    # Quote every leaf line whose unquoted value token is an ambiguous scalar.
    sys.path.insert(0, "/usr/local/lib/hermes-agent")
    import hermes_yaml as _hy  # noqa: E402
    from agent.i18n_layers import non_text_leaves  # noqa: E402

    AMBIGUOUS = {"on", "off", "yes", "no", "true", "false", "null", "~", "y", "n"}

    def _quote_ambiguous(path: Path) -> int:
        fixed = 0
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        for i, ln in enumerate(lines):
            m = re.match(r"^(\s*)([\w.\"'-]+): (.+?)\s*$", ln)
            if not m:
                continue
            indent, key, val = m.groups()
            if val.startswith(("\"", "'")) or val.startswith("{") or val.startswith("["):
                continue
            if val.lower() in AMBIGUOUS:
                lines[i] = f'{indent}{key}: "{val}"\n'
                fixed += 1
        path.write_text("".join(lines), encoding="utf-8")
        return fixed

    for attempt in range(3):
        doc = _hy.safe_load(out_yaml.read_text(encoding="utf-8-sig"))
        bad = non_text_leaves(doc if doc is not None else {})
        if not bad:
            print(f"fixup: clean after {attempt} quote pass(es)")
            break
        print(f"fixup pass {attempt + 1}: non-text leaves {bad[:5]} -> quoting ambiguous scalars")
        n = _quote_ambiguous(out_yaml)
        if n == 0:
            print("fixup: could not locate offending lines — needs manual fix")
            break
    print(f"\nWROTE {out_yaml}")
    n_ok = len(en) - len(missing)
    print(f"vi.yaml keys: {n_ok} (of {len(en)} EN keys)")


if __name__ == "__main__":
    main()
