import importlib.util
import sys
from pathlib import Path
from typing import Any


class PluginManager:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.plugins_dir = self.base_dir / "plugins"
        self.plugins: list[Any] = []
        self.brahma_echo = None

    def load_plugins(self) -> None:
        if not self.plugins_dir.exists():
            return
        for p in sorted(self.plugins_dir.glob("*.py")):
            if p.name.startswith("__"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(p.stem, str(p))
                if not spec or not spec.loader:
                    continue
                mod = importlib.util.module_from_spec(spec)
                sys.modules[p.stem] = mod
                spec.loader.exec_module(mod)
                plugin = getattr(mod, "plugin", None)
                if plugin is None:
                    # fallback: accept module with functions
                    plugin = mod
                self.plugins.append(plugin)
                print(f"[Plugins] Loaded {p.name}")
            except Exception as exc:
                print(f"[Plugins] Failed to load {p.name}: {exc}")

    def register_brahma(self, brahma_obj) -> None:
        self.brahma_echo = brahma_obj
        for p in list(self.plugins):
            try:
                fn = getattr(p, "on_brahma_created", None)
                if callable(fn):
                    fn(brahma_obj)
            except Exception as exc:
                print(f"[Plugins] on_brahma_created error: {exc}")

    def dispatch(self, hook: str, *args, **kwargs):
        """Call hook on plugins. If any plugin returns True, stop and return True."""
        for p in list(self.plugins):
            try:
                fn = getattr(p, hook, None)
                if callable(fn):
                    # call with brahma echo if plugin expects it
                    try:
                        res = fn(*args, **kwargs, brahma_echo=self.brahma_echo)
                    except TypeError:
                        res = fn(*args, **kwargs)
                    if res is True:
                        return True
            except Exception as exc:
                print(f"[Plugins] Hook {hook} error in {getattr(p,'__name__',str(p))}: {exc}")
        return False
