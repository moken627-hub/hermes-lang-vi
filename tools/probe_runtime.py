"""In-process probe: register the vi pack like the loader would, then t()."""
import sys

sys.path.insert(0, "/usr/local/lib/hermes-agent")

from agent.i18n_layers import parse_locale_file, register_pack  # noqa: E402
from agent import i18n  # noqa: E402

msgs = parse_locale_file("/root/5ac/scripts/infra/hermes-lang-vi/locales/vi.yaml")
print("parsed keys:", len(msgs))
register_pack("vi", "core", msgs, source="probe", endonym="Tiếng Việt")
print("vi in supported:", "vi" in i18n.supported_languages())
print("opts sample:", [o for o in i18n.language_options() if o["id"] == "vi"])
print("approval.denied [vi]:", repr(i18n.t("approval.denied", lang="vi")))
print("cron.next_short [vi]:", repr(i18n.t("cli.commands.cron.next_short", lang="vi")))
print("yolo.enabled [vi]:", i18n.t("gateway.yolo.enabled", lang="vi")[:70])
print("choose_long [vi]:", repr(i18n.t("approval.choose_long", lang="vi")))
print("resolve vi:", i18n.resolve_language_id("vi"))
