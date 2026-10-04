# Port Range Expander

Expand comma-and-dash port specifications like `"80,443,8000-8100"` into a sorted list of individual port numbers.

```python
from port_range_expander import expand, expand_unique, parse_tokens, PortRangeError

expand("80,443,8000-8100")        # -> [80, 443, 8000, 8001, ..., 8100]
expand_unique("80,80,443")          # -> {80, 443}
parse_tokens("80,443,8000-8100")     # -> [80, 443, (8000, 8100)]

try:
    expand("8100-8000")
except PortRangeError as e:
    print(e)  # range start greater than end: 8100-8000
```

## Why this exists

Config files, firewalls, and log scrapers all describe ports with a small DSL: commas for lists, dashes for ranges. Pasting that DSL into Python usually means a one-off `split` that forgets to sort, dedupe, or validate. This library does exactly those three things and nothing else.

The trade-off is strictness. A spec like `"80, 443"` (note the space) is rejected rather than silently trimmed, because in real configs a stray space after a comma usually masks a typo, not an intent. Leading zeros (`"080"`) are rejected for the same reason. If you want lenient parsing, normalise the string yourself before calling `expand`.

## Exported names

- `expand(spec: str) -> list[int]` — sorted, de-duplicated port list.
- `expand_unique(spec: str) -> set[int]` — same as `expand` but as a set, no ordering.
- `parse_tokens(spec: str) -> list[int | tuple[int, int]]` — structural view, does not expand ranges.
- `PortRangeError` — subclass of `ValueError`, raised on any malformed input.

## Awkward edges

- Whitespace anywhere in the spec raises `PortRangeError`. Strip it upstream if your source is human-typed config.
- `"8100-8000"` raises; ranges must be ascending. Descending intent is not supported — sort it yourself if you need that.
- Port `0` is accepted; it is a valid IANA port even if rarely used.
- `65536` and above raise. So do negative values.
- Trailing commas (`"80,"`) raise; there is no "ignore empty tokens" mode.

## Running the tests

```
PYTHONPATH=src python -m unittest discover -s tests
```
