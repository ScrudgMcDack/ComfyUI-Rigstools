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


def debug_enabled():
    """Settings → Rigstools → Debug: the nodes write details of their work to the console."""
    return setting_on("Rigstools.Debug.Log")


def debug(message):
    if debug_enabled():
        logger.info(message)
