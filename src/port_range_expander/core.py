"""Core parsing logic for port range expansion.

Design choices:

- Whitespace inside the spec is forbidden by design. Allowing '80, 443' tends to
  mask typos in config files where the intent was a single token, not a spaced
  list. The error is surfaced explicitly rather than silently normalised.

- A single token with a dash must expand to a real ascending range; '8100-8000'
  is rejected because it almost always indicates a swapped bound, not a
  descending intent. If a caller genuinely needs descending, they can sort
  themselves; this library owns one direction.

- Endpoints of a range are inclusive on both sides. That is the universal
  convention for port range notation (e.g. iptables, nginx) and departing from
  it would surprise every reader.

- Duplicates are collapsed. '80,80' returning [80, 80] would just force every
  caller to de-duplicate.
"""

from __future__ import annotations

from typing import Union


_MAX_PORT = 65535
_MIN_PORT = 0


class PortRangeError(ValueError):
    """Raised when a port specification is malformed or out of range."""


def _parse_single(text: str) -> int:
    """Parse a single decimal port number.

    We reject leading zeros ('080') because they are a classic source of
    copy-paste bugs and octal confusion, and a port number is never written
    with a leading zero in any sane configuration format.
    """
    if not text:
        raise PortRangeError("empty port number")
    if not text.isdigit():
        raise PortRangeError(f"invalid port number: {text!r}")
    if len(text) > 1 and text[0] == "0":
        raise PortRangeError(f"leading zero not permitted in port: {text!r}")
    value = int(text)
    if not _MIN_PORT <= value <= _MAX_PORT:
        raise PortRangeError(
            f"port out of range [{_MIN_PORT}, {_MAX_PORT}]: {value}"
        )
    return value


def _parse_token(token: str) -> Union[int, tuple[int, int]]:
    """Parse one comma-delimited token into either an int or a (lo, hi) pair."""
    if not token:
        raise PortRangeError("empty token")
    if token.startswith("-") or token.endswith("-"):
        raise PortRangeError(f"dangling dash in token: {token!r}")
    parts = token.split("-")
    if len(parts) == 1:
        return _parse_single(parts[0])
    if len(parts) == 2:
        lo = _parse_single(parts[0])
        hi = _parse_single(parts[1])
        if lo > hi:
            raise PortRangeError(
                f"range start greater than end: {lo}-{hi}"
            )
        return (lo, hi)
    raise PortRangeError(f"multiple dashes in token: {token!r}")


def parse_tokens(spec: str) -> list[Union[int, tuple[int, int]]]:
    """Split *spec* on commas and return a list of parsed tokens.

    Each token is returned as either an ``int`` (single port) or a
    ``(lo, hi)`` tuple (inclusive range). This function does not expand
    ranges; it is useful when a caller wants to inspect the structure of a
    spec without materialising every port.
    """
    if not isinstance(spec, str):
        raise PortRangeError(f"spec must be a string, got {type(spec).__name__}")
    if spec == "":
        return []
    if any(ch.isspace() for ch in spec):
        raise PortRangeError("whitespace not permitted in port spec")
    return [_parse_token(tok) for tok in spec.split(",")]


def expand_unique(spec: str) -> set[int]:
    """Expand *spec* into a :class:`set` of individual port numbers.

    Returns an empty set for an empty string. Raises
    :class:`PortRangeError` on any malformed token or out-of-range port.
    """
    tokens = parse_tokens(spec)
    ports: set[int] = set()
    for tok in tokens:
        if isinstance(tok, int):
            ports.add(tok)
        else:
            lo, hi = tok
            # Ranges are inclusive and ascending; the size of a valid range
            # is bounded by _MAX_PORT+1, so a plain loop is both clear and
            # cheap enough. No need for range arithmetic.
            ports.update(range(lo, hi + 1))
    return ports


def expand(spec: str) -> list[int]:
    """Expand *spec* into a sorted list of individual port numbers.

    Equivalent to ``sorted(expand_unique(spec))`` but returns the canonical
    sorted list directly, which is what the overwhelming majority of callers
    want for display or downstream iteration.
    """
    return sorted(expand_unique(spec))
