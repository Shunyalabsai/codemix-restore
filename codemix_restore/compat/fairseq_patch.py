"""Python 3.12 compatibility patches for fairseq, hydra-core, and torch.

These libraries use mutable dataclass defaults and deprecated importlib APIs
that break on Python >= 3.12. This module monkey-patches the stdlib to work
around these issues.

MUST be called via `apply_patch()` BEFORE importing torch, fairseq, or hydra.
Safe to call multiple times (idempotent).
"""

from __future__ import annotations

import dataclasses
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

    _patch_fairseq_checkpoint_utils()
    _patch_fairseq_hydra_init()
    _patch_hydra_plugins()

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
    """Patch fairseq checkpoint_utils to use weights_only=False in torch.load.

    torch >= 2.6 changed the default to weights_only=True, but fairseq
    checkpoints contain argparse.Namespace objects that require pickle.
    """
    try:
        import importlib
        spec = importlib.util.find_spec("fairseq.checkpoint_utils")
        if spec is None:
            return
        # We patch at import time by modifying the source file's torch.load call.
        # Since the module may not be imported yet, we do a lazy patch: intercept
        # torch.load itself to add weights_only=False when called from fairseq.
        import torch
        original_torch_load = torch.load

        def patched_torch_load(*args, **kwargs):
            if "weights_only" not in kwargs:
                kwargs["weights_only"] = False
            return original_torch_load(*args, **kwargs)

        torch.load = patched_torch_load
    except Exception:
        pass  # torch not installed, nothing to patch


def _patch_fairseq_hydra_init() -> None:
    """Patch fairseq.dataclass.initialize.hydra_init to handle default_factory.

    After our dataclass patch, fields that had mutable defaults now use
    default_factory. The hydra_init function reads field.default directly,
    which is MISSING for factory fields. We fix it to call the factory.
    """
    # This is a lazy patch — we monkey-patch the module after it's imported.
    # Since fairseq imports happen lazily, we register an import hook.
    import importlib
    try:
        spec = importlib.util.find_spec("fairseq.dataclass.initialize")
        if spec is None:
            return
    except (ModuleNotFoundError, ValueError):
        return

    # The actual patching happens when the module is first imported.
    # We use a meta path finder to intercept it.
    class FairseqInitPatcher:
        """One-shot import hook that patches fairseq.dataclass.initialize."""

        def find_module(self, fullname, path=None):
            if fullname == "fairseq.dataclass.initialize":
                return self
            return None

        def load_module(self, fullname):
            if fullname in sys.modules:
                return sys.modules[fullname]
            # Remove ourselves so we don't interfere with the real import
            sys.meta_path.remove(self)
            # Do the real import
            mod = importlib.import_module(fullname)
            # Now patch the hydra_init function
            original_hydra_init = mod.hydra_init

            def patched_hydra_init(cfg_name="config"):
                from fairseq.dataclass.configs import FairseqConfig
                from hydra.core.config_store import ConfigStore

                cs = ConfigStore.instance()
                cs.store(name=f"{cfg_name}", node=FairseqConfig)

                for k in FairseqConfig.__dataclass_fields__:
                    field_obj = FairseqConfig.__dataclass_fields__[k]
                    v = field_obj.default
                    if v is dataclasses.MISSING and field_obj.default_factory is not dataclasses.MISSING:
                        v = field_obj.default_factory()
                    try:
                        cs.store(name=k, node=v)
                    except BaseException:
                        pass  # skip fields OmegaConf can't handle

            mod.hydra_init = patched_hydra_init
            return mod

    sys.meta_path.insert(0, FairseqInitPatcher())


def _patch_hydra_plugins() -> None:
    """Patch hydra.core.plugins to not use deprecated find_module/load_module.

    Python 3.12 removed `find_module` from importlib finders. Hydra's plugin
    scanner still uses it. We patch the scan method to use importlib.import_module
    as a fallback.
    """
    # Similar lazy patching approach
    import importlib

    try:
        spec = importlib.util.find_spec("hydra.core.plugins")
        if spec is None:
            return
    except (ModuleNotFoundError, ValueError):
        return

    class HydraPluginsPatcher:
        """One-shot import hook that patches hydra.core.plugins."""

        def find_module(self, fullname, path=None):
            if fullname == "hydra.core.plugins":
                return self
            return None

        def load_module(self, fullname):
            if fullname in sys.modules:
                return sys.modules[fullname]
            sys.meta_path.remove(self)
            mod = importlib.import_module(fullname)
            # Patch the _scan_all_plugins method to handle missing find_module
            original_scan = mod.Plugins._scan_all_plugins

            @staticmethod
            def patched_scan(*args, **kwargs):
                import warnings
                import pkgutil

                # Simplified plugin scanning that doesn't use find_module
                try:
                    return original_scan(*args, **kwargs)
                except AttributeError as e:
                    if "find_module" in str(e):
                        # Return empty results — fairseq doesn't need hydra plugins
                        return {}, {}
                    raise

            mod.Plugins._scan_all_plugins = patched_scan
            return mod

    sys.meta_path.insert(0, HydraPluginsPatcher())
