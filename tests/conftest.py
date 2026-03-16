"""
Patch broken system-level dependencies before any test module is imported.
The `google.genai` and `supabase` packages fail to load in this environment
due to a broken cffi/cryptography installation. We stub them out here so that
unit tests which mock at the function level can still be collected and run.
"""
import sys
from unittest.mock import MagicMock


def _mock_module(*parts):
    """Register a MagicMock for a dotted module path and all its parents."""
    for i in range(1, len(parts) + 1):
        name = ".".join(parts[:i])
        if name not in sys.modules:
            sys.modules[name] = MagicMock()


# google-genai
_mock_module("google")
_mock_module("google", "genai")
_mock_module("google", "genai", "types")

# supabase
_mock_module("supabase")

# openai
_mock_module("openai")

# anthropic
_mock_module("anthropic")
