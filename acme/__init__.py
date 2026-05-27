"""Acme example plugin package.

The core's plugin loader does `import_module("acme")` and calls the module's
`register()`, so the package must expose it. Re-export from plugin.py.
"""
from .plugin import register

__all__ = ["register"]
