"""Lacon: an AI that thinks in as few letters as possible, recursively over a long context.

The whole package is self-contained: there is no network call and no external model. `Lacon.ask`
is the API, `python -m lacon` is the command line.
"""

from .pebble_context import PebbleContextError
from .rlm import Answer, Lacon

__all__ = ["Answer", "Lacon", "PebbleContextError"]
__version__ = "0.1.0"