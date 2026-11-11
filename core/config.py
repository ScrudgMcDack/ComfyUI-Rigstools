import os
import logging


def _env(name: str, default):
    # RIGSTOOLS_* variables; the old CRYSTOOLS_* names are still honoured
    return os.environ.get(f"RIGSTOOLS_{name}", os.environ.get(f"CRYSTOOLS_{name}", default))


CONFIG = {
    "loglevel": int(_env("LOGLEVEL", logging.INFO)),
    "indent": int(_env("INDENT", 2)),
}
