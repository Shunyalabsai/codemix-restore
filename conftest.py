"""Root conftest: apply Python 3.12 compat patches before any fairseq/hydra imports."""
from codemix_restore.compat.fairseq_patch import apply_patch

apply_patch()
