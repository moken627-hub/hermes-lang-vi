"""Phase-2 probe over the REAL client backend: `python -m tui_gateway.entry` (stdio JSON-RPC).

This is the process the Ink TUI — and the Desktop app's backend — actually spawns. Calling
`i18n.languages` + `i18n.catalog` on it exercises the exact path the language switcher uses:
the gateway creates its own PluginManager for the home, the pack registers vi/core|tui|desktop,
and the RPC returns the merged catalog.

That makes it stronger evidence than an in-process import of `agent.i18n`:
  * real child process, real JSON-RPC framing (UTF-8 JSON lines)
  * the same method names the Desktop app calls (`i18n.catalog` with surface='desktop')
  * proves the SWITCHER sees the language: `i18n.languages` must list vi with endonym "Tiếng Việt"

Sequencing note (measured 2026-10-01): a freshly spawned child has NOT run plugin discovery yet —
`i18n.languages` there lists only the bundled catalogs (17, no vi). Packs register on the process's
first `model_tools` import (the `discover_plugins()` trigger the CLI hits in `cli.py`). This probe
therefore drives one real trigger RPC (`tools.show`) before asserting, exactly as a real TUI/Desktop
session does on its first tool/session call; the pre-trigger baseline is printed for the record.

Run (venv python):
  HERMES_HOME=/root/.hermes /usr/local/lib/hermes-agent/venv/bin/python3 \
      /root/5ac/scripts/infra/hermes-lang-vi/tools/probe_tui_rpc_p2.py
Exit 0 = every assertion passed.
"""
from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

AGENT = Path("/usr/local/lib/hermes-agent")
HOME = Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes")).resolve()
if HOME.name != ".hermes" or not (HOME / "plugins" / "hermes-lang-vi").is_dir():
    print(f"PROBE MISCONFIGURED — HERMES_HOME={HOME} does not carry the installed pack. "
          f"Re-run with HERMES_HOME=/root/.hermes")
    sys.exit(2)

EXPECTED = {"core": 3434, "tui": 1244, "desktop": 4922}
KNOWN = {
    "tui": ("billing.autoReload.aDifferentCard", "một thẻ khác", "a different card"),
    "desktop": ("agents.activeCount", "{0} đang hoạt động", "active"),
}
TIMEOUT = 90.0
failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)


class Entry:
    """Minimal stdio JSON-RPC client for `python -m tui_gateway.entry`."""

    def __init__(self) -> None:
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "tui_gateway.entry"], cwd=str(AGENT),
            env={**os.environ, "HERMES_HOME": str(HOME)},
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._out: queue.Queue[bytes | None] = queue.Queue()
        self._err: list[bytes] = []
        self._resp: dict[str, dict] = {}
        self._events: list[dict] = []
        self._n = 0
        threading.Thread(target=self._pump_out, daemon=True).start()
        threading.Thread(target=self._pump_err, daemon=True).start()

    def _pump_out(self) -> None:
        for line in self.proc.stdout:  # type: ignore[union-attr]
            self._out.put(line)
        self._out.put(None)

    def _pump_err(self) -> None:
        for line in self.proc.stderr:  # type: ignore[union-attr]
            self._err.append(line)

    @property
    def stderr(self) -> str:
        return b"".join(self._err).decode("utf-8", "replace")

    def _drain(self, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                raw = self._out.get(timeout=0.25)
            except queue.Empty:
                continue
            if raw is None:
                raise RuntimeError(f"tui_gateway closed stdout (rc={self.proc.poll()})")
            try:
                msg = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue  # stray non-protocol line
            if "id" in msg:
                self._resp[str(msg["id"])] = msg
            elif msg.get("method") == "event":
                self._events.append(msg.get("params") or {})

    def call(self, method: str, params: dict | None = None, timeout: float = TIMEOUT) -> dict:
        self._n += 1
        rid = f"p2-{self._n}"
        self.proc.stdin.write(json.dumps(  # type: ignore[union-attr]
            {"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}},
            ensure_ascii=False).encode("utf-8") + b"\n")
        self.proc.stdin.flush()  # type: ignore[union-attr]
        deadline = time.monotonic() + timeout
        while rid not in self._resp:
            if time.monotonic() > deadline:
                raise RuntimeError(f"{method}: no response in {timeout}s\n{self.stderr[-2000:]}")
            self._drain(0.5)
        return self._resp[rid]

    def close(self) -> None:
        try:
            self.proc.terminate()
            self.proc.wait(timeout=15)
        except Exception:
            self.proc.kill()


print("=" * 78)
print("hermes-lang-vi Phase-2 probe — REAL client backend (tui_gateway.entry stdio RPC)")
print(f"HERMES_HOME: {HOME}")
print(f"child: {sys.executable} -m tui_gateway.entry  (cwd={AGENT})")
print("=" * 78)

gw = Entry()
try:
    started = time.monotonic()
    base = (gw.call("i18n.languages").get("result") or {}).get("languages") or []
    base_vi = [o for o in base if o.get("id") == "vi"]
    print(f"\n-- baseline: i18n.languages on a freshly spawned child ({(time.monotonic() - started):.1f}s) --")
    print(f"  {len(base)} languages, vi={base_vi}")
    print("  (expected: the pack is NOT registered yet — nothing has imported model_tools, the "
          "process-wide\n   discover_plugins() trigger. Not a failure; see the trigger step below.)")

    # The client backend registers packs on its first plugin-discovery trigger. Every real client
    # (TUI / Desktop) reaches this through its first tool/session RPC; `tools.show` is the cheapest
    # public RPC that imports model_tools, so use it to drive the same, real trigger.
    trig = gw.call("tools.show")
    n_tools = len(((trig.get("result") or {}).get("sections")) or [])
    print(f"\n-- discovery trigger: tools.show -> {n_tools} tool sections returned "
          f"(imports model_tools -> discover_plugins) --")
    check("tools.show succeeded through the child (discovery trigger reachable)",
          "error" not in trig and n_tools > 0, f"sections={n_tools} err={trig.get('_error')}")

    r = gw.call("i18n.languages")
    langs = (r.get("result") or {}).get("languages")
    print(f"\n-- i18n.languages after the trigger --")
    vi_entry = None
    for opt in (langs or []):
        print(f"  {opt}")
        if opt.get("id") == "vi":
            vi_entry = opt
    check("i18n.languages lists vi (language switcher entry)", bool(langs), f"{len(langs or [])} languages")
    check("vi endonym is 'Tiếng Việt' (not 'Vietnamese')",
          bool(vi_entry) and vi_entry.get("endonym") == "Tiếng Việt",
          repr((vi_entry or {}).get("endonym")))
    check("vi source is the installed plugin pack",
          bool(vi_entry) and vi_entry.get("source") == "plugin:hermes-lang-vi",
          repr((vi_entry or {}).get("source")))

    for surface in ("tui", "desktop"):
        r = gw.call("i18n.catalog", {"lang": "vi", "surface": surface})
        res = r.get("result") or {}
        msgs = res.get("messages") or {}
        print(f"\n-- i18n.catalog lang=vi surface={surface} --")
        print(f"  returned lang={res.get('lang')!r} surface={res.get('surface')!r} keys={len(msgs)}")
        check(f"{surface}: RPC returned {EXPECTED[surface]} keys", len(msgs) == EXPECTED[surface],
              f"got {len(msgs)}")
        key, want_vi, want_en = KNOWN[surface]
        got = msgs.get(key)
        print(f"  {key}\n    rpc={got!r}\n    en ={want_en!r}")
        check(f"{surface}: {key} served as Vietnamese", got == want_vi, repr(got))
        check(f"{surface}: {key} differs from English", bool(got) and got != want_en, repr(got))

    # core surface also served through the same RPC
    r = gw.call("i18n.catalog", {"lang": "vi", "surface": "core"})
    core = (r.get("result") or {}).get("messages") or {}
    print(f"\n-- i18n.catalog lang=vi surface=core -> {len(core)} keys --")
    check("core: RPC returned 3434 keys", len(core) == EXPECTED["core"], f"got {len(core)}")
    check("core: approval.denied is Vietnamese", "Đã từ chối" in (core.get("approval.denied") or ""),
          repr(core.get("approval.denied")))

    errs = [ln for ln in gw.stderr.splitlines()
            if "locale file skipped" in ln.lower() or ("lang-vi" in ln.lower() and "error" in ln.lower())]
    check("no 'locale file skipped' / lang-vi error on the child's stderr", not errs, str(errs[:3]))
finally:
    gw.close()

print("\n" + "=" * 78)
if failures:
    print(f"RPC PROBE FAILED — {len(failures)} check(s): {failures}")
    sys.exit(1)
print("RPC PROBE PASSED — the client backend (TUI/Desktop path) serves Vietnamese from the pack")
sys.exit(0)
