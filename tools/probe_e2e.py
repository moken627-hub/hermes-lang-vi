"""End-to-end probe: fresh process, real config, real installed pack."""
import sys

sys.path.insert(0, "/usr/local/lib/hermes-agent")

from hermes_cli.plugins import PluginManager  # noqa: E402

pm = PluginManager()
pm.discover_and_load()

from agent import i18n  # noqa: E402

lang = i18n.get_language()
print("resolved language:", lang)
print("vi in supported:", "vi" in i18n.supported_languages())
opts = [o for o in i18n.language_options() if o["id"] == "vi"]
print("picker entry:", opts)
print("approval.denied:", repr(i18n.t("approval.denied")))
print("cli.commands.cron.next_short:", repr(i18n.t("cli.commands.cron.next_short")))
print("gateway.yolo.enabled:", i18n.t("gateway.yolo.enabled")[:70])
print("approval.choose_long:", repr(i18n.t("approval.choose_long")))
print("display.failure.file_not_found:", i18n.t("display.failure.file_not_found"))
