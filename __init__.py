"""hermes-lang-vi — Vietnamese language pack for Hermes Agent (core surface).

Registration is driven by the manifest: ``provides_locales`` makes the plugin
loader call ``register_locale_dir`` on ``locales/`` automatically. ``register``
exists only to satisfy the loader's ``__init__.py`` requirement.
"""


def register(ctx):  # noqa: ARG001 - ctx unused by design
    """No-op: the loader registers locales/ from the manifest's provides_locales."""
    return None
