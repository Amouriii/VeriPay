"""veripay_common: shared, read-only contract surface for all VeriPay services.

This package is the narrow coordination boundary for parallel work-trees.
Changes here land on `main` first and are rebased by all work-trees.
"""

from veripay_common import constants, enums  # noqa: F401

__all__ = ["constants", "enums"]
__version__ = "0.1.0"
