"""ComfyUI settings of Rigstools (Settings → Rigstools), read from the settings file of the default user."""
import os
import json
from .logger import logger


def _user_dir():
    try:
        import folder_paths
        return folder_paths.get_user_directory()
    except Exception:
        return os.path.join(os.path.dirname(__file__), "..", "user")


def setting_on(key):
    """A boolean setting."""
    try:
        with open(os.path.join(_user_dir(), "default", "comfy.settings.json"), "r", encoding="utf-8") as fh:
            return json.load(fh).get(key) is True
    except (OSError, ValueError, AttributeError):
        return False


def setting_value(key, default=None):
    """Any setting; `default` when it was never changed (ComfyUI stores only changed values)."""
    try:
        with open(os.path.join(_user_dir(), "default", "comfy.settings.json"), "r", encoding="utf-8") as fh:
            return json.load(fh).get(key, default)
    except (OSError, ValueError, AttributeError):
        return default


def gallery_enabled():
    """Settings → Rigstools → Gallery → Use the gallery (on by default). Off: no button, no indexing, no page."""
    return setting_value("Rigstools.Gallery.Enabled", True) is not False


AUTO_SCAN_CHOICES = (0, 10, 30, 60)


def gallery_auto_scan():
    """Settings → Rigstools → PicoTeka → Auto refresh: seconds between scans while the gallery page is open and seen
    (0 = off; the scan after each finished run happens anyway)."""
    try:
        v = int(setting_value("Rigstools.Gallery.AutoScan", 10))
    except (TypeError, ValueError):
        return 10
    return v if v in AUTO_SCAN_CHOICES else 10


def debug_enabled():
    """Settings → Rigstools → Debug: the nodes write details of their work to the console."""
    return setting_on("Rigstools.Debug.Log")


def debug(message):
    if debug_enabled():
        logger.info(message)
