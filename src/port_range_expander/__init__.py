"""Port Range Expander.

Expand comma-and-dash port specifications like '80,443,8000-8100'
into a sorted set of individual port numbers.

Public API:
    expand(spec)          -> list[int]
    expand_unique(spec)   -> set[int]
    parse_tokens(spec)    -> list[int | tuple[int, int]]
    PortRangeError        -> raised on malformed input
"""

from .core import (
    PortRangeError,
    expand,
    expand_unique,
    parse_tokens,
)

__all__ = [
    "PortRangeError",
    "expand",
    "expand_unique",
    "parse_tokens",
]
