"""Run-time values of other nodes: what they output in the current run, read from ComfyUI's execution cache.

When our save node runs, every node above it has already run, and its outputs sit in the output cache of the
executor. The cache is internal to ComfyUI (not a public API), so everything here is best effort: when it is not
available (another ComfyUI version, an output evicted from the cache) the caller falls back to the graph walk."""
import gc

from .logger import logger

_executor = None


def _install():
    """Remember the executor ComfyUI creates (it is created after the custom nodes are loaded)."""
    try:
        import execution
        cls = execution.PromptExecutor
        if getattr(cls, "_rigstools_patched", False):
            return
        orig = cls.__init__

        def __init__(self, *args, **kwargs):
            global _executor
            orig(self, *args, **kwargs)
            _executor = self

        cls.__init__ = __init__
        cls._rigstools_patched = True
    except Exception as e:
        logger.debug(f"runtime values: executor hook not installed: {e}")


def _find_executor():
    global _executor
    if _executor is None:
        try:
            import execution
            _executor = next((o for o in gc.get_objects() if isinstance(o, execution.PromptExecutor)), None)
        except Exception:
            _executor = None
    return _executor


class Outputs:
    """Reads node outputs of the current run. output(node_id, slot) -> the value, or MISSING."""
    MISSING = object()

    def __init__(self):
        ex = _find_executor()
        self.cache = getattr(getattr(ex, "caches", None), "outputs", None)

    def __bool__(self):
        return self.cache is not None and hasattr(self.cache, "get_local")

    def output(self, node_id, slot):
        if not self:
            return self.MISSING
        try:
            entry = self.cache.get_local(str(node_id))
        except Exception:
            return self.MISSING
        if entry is None:
            return self.MISSING
        outs = getattr(entry, "outputs", entry)       # CacheEntry(ui, outputs) or, in older versions, the list
        try:
            values = outs[slot]
        except Exception:
            return self.MISSING
        if isinstance(values, (list, tuple)):
            if len(values) != 1:                       # a list output with several values: no single value
                return self.MISSING
            values = values[0]
        return values


_install()
