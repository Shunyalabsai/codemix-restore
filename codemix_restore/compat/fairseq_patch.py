"""Python 3.12 compatibility patches for fairseq, hydra-core, and torch.

These libraries use mutable dataclass defaults and deprecated importlib APIs
that break on Python >= 3.12. This module monkey-patches the stdlib to work
around these issues.

MUST be called via `apply_patch()` BEFORE importing torch, fairseq, or hydra.
Safe to call multiple times (idempotent).
"""

from __future__ import annotations

import dataclasses
import importlib
import importlib.abc
import importlib.machinery
import logging
import sys

logger = logging.getLogger(__name__)

_PATCHED = False


def apply_patch() -> None:
    """Apply all Python 3.12 compatibility patches. Idempotent."""
    global _PATCHED
    if _PATCHED:
        return

    if sys.version_info >= (3, 11):
        _patch_dataclasses()

    # Register import hooks BEFORE any imports that could trigger the chain.
    _patch_fairseq_hydra_init()
    _patch_hydra_plugins()
    _patch_fairseq_checkpoint_utils()

    _PATCHED = True
    logger.debug("fairseq/hydra/torch Python 3.12 patches applied")


def _patch_dataclasses() -> None:
    """Patch dataclasses._get_field to tolerate mutable defaults.

    fairseq and hydra use patterns like:
        @dataclass
        class Cfg:
            sub: SubConfig = SubConfig()          # raw mutable default
            other: SubConfig = field(default=SubConfig())  # mutable in field()

    Python >= 3.11 rejects both. We intercept the error and auto-wrap
    the mutable value in default_factory.
    """
    original_get_field = dataclasses._get_field

    def patched_get_field(cls, a_name, a_type, kw_only):
        try:
            return original_get_field(cls, a_name, a_type, kw_only)
        except (ValueError, TypeError) as e:
            msg = str(e)
            if "mutable default" not in msg and "default factory" not in msg:
                raise

            default = cls.__dict__.get(a_name, dataclasses.MISSING)

            if isinstance(default, dataclasses.Field):
                # field(default=MutableObj()) — rewrap with default_factory
                if default.default is not dataclasses.MISSING:
                    mutable_val = default.default
                    new_field = dataclasses.field(
                        default_factory=lambda d=mutable_val: d,
                        init=default.init,
                        repr=default.repr,
                        hash=default.hash,
                        compare=default.compare,
                        metadata=default.metadata,
                        kw_only=default.kw_only,
                    )
                    setattr(cls, a_name, new_field)
                else:
                    raise
            elif default is not dataclasses.MISSING:
                # Raw mutable default on the class
                mutable_val = default
                setattr(cls, a_name, dataclasses.field(
                    default_factory=lambda d=mutable_val: d,
                ))
            else:
                raise

            return original_get_field(cls, a_name, a_type, kw_only)

    dataclasses._get_field = patched_get_field


def _patch_fairseq_checkpoint_utils() -> None:
    """Patch torch.load to use weights_only=False by default.

    torch >= 2.6 changed the default to weights_only=True, but fairseq
    checkpoints contain argparse.Namespace objects that require pickle.
    """
    try:
        import torch
        original_torch_load = torch.load

        def patched_torch_load(*args, **kwargs):
            if "weights_only" not in kwargs:
                kwargs["weights_only"] = False
            return original_torch_load(*args, **kwargs)

        torch.load = patched_torch_load
    except ImportError:
        pass  # torch not installed, nothing to patch


# ---------------------------------------------------------------------------
# fairseq.dataclass.initialize patch
# ---------------------------------------------------------------------------

def _patched_hydra_init(cfg_name="config"):
    """Replacement hydra_init that handles default_factory and MISSING fields."""
    from fairseq.dataclass.configs import FairseqConfig
    from hydra.core.config_store import ConfigStore

    cs = ConfigStore.instance()
    cs.store(name=f"{cfg_name}", node=FairseqConfig)

    for k in FairseqConfig.__dataclass_fields__:
        field_obj = FairseqConfig.__dataclass_fields__[k]
        v = field_obj.default
        if v is dataclasses.MISSING:
            if field_obj.default_factory is not dataclasses.MISSING:
                v = field_obj.default_factory()
            else:
                # Truly required field with no default — skip it
                continue
        try:
            cs.store(name=k, node=v)
        except BaseException:
            pass  # skip fields OmegaConf can't handle


def _patch_fairseq_hydra_init() -> None:
    """Patch fairseq.dataclass.initialize.hydra_init to handle default_factory.

    Uses a meta path finder with find_spec (modern API) to intercept the import
    of fairseq.dataclass.initialize and replace hydra_init before fairseq.__init__
    calls it.
    """
    # If already imported, patch directly
    if "fairseq.dataclass.initialize" in sys.modules:
        sys.modules["fairseq.dataclass.initialize"].hydra_init = _patched_hydra_init
        return

    class FairseqInitPatcher(importlib.abc.MetaPathFinder, importlib.abc.Loader):
        """One-shot meta path finder that patches fairseq.dataclass.initialize."""

        def __init__(self):
            self._real_loader = None

        def find_spec(self, fullname, path, target=None):
            if fullname != "fairseq.dataclass.initialize":
                return None
            # Remove ourselves to avoid infinite recursion
            if self in sys.meta_path:
                sys.meta_path.remove(self)
            # Find the real spec using the remaining finders
            real_spec = importlib.util.find_spec(fullname)
            if real_spec is None:
                return None
            # Save the real loader for exec_module
            self._real_loader = real_spec.loader
            # Return a spec that uses us as the loader wrapper
            return importlib.machinery.ModuleSpec(
                fullname,
                self,
                origin=real_spec.origin,
                is_package=False,
            )

        def create_module(self, spec):
            return None  # use default module creation

        def exec_module(self, module):
            # Execute the real module code first
            if self._real_loader:
                self._real_loader.exec_module(module)
            # Now patch hydra_init
            module.hydra_init = _patched_hydra_init

    sys.meta_path.insert(0, FairseqInitPatcher())


# ---------------------------------------------------------------------------
# hydra.core.plugins patch
# ---------------------------------------------------------------------------

def _patch_hydra_plugins() -> None:
    """Patch hydra.core.plugins to handle removed find_module in Python 3.12."""
    if "hydra.core.plugins" in sys.modules:
        _do_patch_hydra_plugins(sys.modules["hydra.core.plugins"])
        return

    class HydraPluginsPatcher(importlib.abc.MetaPathFinder, importlib.abc.Loader):
        """One-shot meta path finder that patches hydra.core.plugins."""

        def __init__(self):
            self._real_loader = None

        def find_spec(self, fullname, path, target=None):
            if fullname != "hydra.core.plugins":
                return None
            if self in sys.meta_path:
                sys.meta_path.remove(self)
            real_spec = importlib.util.find_spec(fullname)
            if real_spec is None:
                return None
            self._real_loader = real_spec.loader
            return importlib.machinery.ModuleSpec(
                fullname,
                self,
                origin=real_spec.origin,
                is_package=False,
            )

        def create_module(self, spec):
            return None

        def exec_module(self, module):
            if self._real_loader:
                self._real_loader.exec_module(module)
            _do_patch_hydra_plugins(module)

    sys.meta_path.insert(0, HydraPluginsPatcher())


def _do_patch_hydra_plugins(mod) -> None:
    """Patch _scan_all_plugins to handle missing find_module in Python 3.12.

    The original code uses `importer.find_module(modname)` which fails on
    Python 3.12 because FileFinder no longer has find_module. We patch the
    scanner to use importlib.import_module as fallback.
    """
    if not hasattr(mod, 'Plugins'):
        return

    import inspect
    import pkgutil
    import warnings
    from collections import defaultdict
    from timeit import default_timer as timer

    from hydra.plugins.plugin import Plugin
    from hydra.plugins.config_source import ConfigSource
    from hydra.plugins.completion_plugin import CompletionPlugin
    from hydra.plugins.launcher import Launcher
    from hydra.plugins.sweeper import Sweeper
    from hydra.plugins.search_path_plugin import SearchPathPlugin

    @staticmethod
    def patched_scan(modules):
        stats = mod.ScanStats()
        stats.total_time = timer()

        ret = defaultdict(list)
        plugin_types = [Plugin, ConfigSource, CompletionPlugin, Launcher, Sweeper, SearchPathPlugin]

        for mdl in modules:
            for importer, modname, ispkg in pkgutil.walk_packages(
                path=mdl.__path__, prefix=mdl.__name__ + ".", onerror=lambda x: None
            ):
                try:
                    module_name = modname.rsplit(".", 1)[-1]
                    if module_name.startswith("_") and not module_name.startswith("__"):
                        continue

                    import_time = timer()
                    # Use importlib.import_module directly (works on all Python versions)
                    with warnings.catch_warnings(record=True) as recorded_warnings:
                        loaded_mod = importlib.import_module(modname)
                    import_time = timer() - import_time

                    if len(recorded_warnings) > 0:
                        import sys as _sys
                        _sys.stderr.write(
                            f"[Hydra plugins scanner] : warnings from '{modname}'.\n"
                        )

                    stats.total_modules_import_time += import_time
                    stats.modules_import_time[modname] = import_time

                    if loaded_mod is not None:
                        for name, obj in inspect.getmembers(loaded_mod):
                            if (
                                inspect.isclass(obj)
                                and issubclass(obj, Plugin)
                                and not inspect.isabstract(obj)
                            ):
                                for plugin_type in plugin_types:
                                    if issubclass(obj, plugin_type):
                                        ret[plugin_type].append(obj)
                except ImportError as e:
                    warnings.warn(
                        message=f"\n\tError importing '{modname}'.\n"
                        f"\tPlugin is incompatible with this Hydra version or buggy.\n"
                        f"\t\t{type(e).__name__} : {e}",
                        category=UserWarning,
                    )

        stats.total_time = timer() - stats.total_time
        return ret, stats

    mod.Plugins._scan_all_plugins = patched_scan
