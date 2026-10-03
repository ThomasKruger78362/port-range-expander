"""Tests for port_range_expander.core.

These cover the happy path and the awkward edges the implementation actually
handles: whitespace, leading zeros, dangling dashes, swapped bounds, out of
range values, and duplicates. No test asserts behaviour the code does not
claim to provide.
"""

import unittest

from port_range_expander import (
    PortRangeError,
    expand,
    expand_unique,
    parse_tokens,
)


class ExpandTests(unittest.TestCase):
    def test_single_port(self):
        self.assertEqual(expand("80"), [80])

    def test_comma_list(self):
        self.assertEqual(expand("80,443,8080"), [80, 443, 8080])

    def test_single_range(self):
        self.assertEqual(expand("8000-8002"), [8000, 8001, 8002])

    def test_mixed_single_and_range(self):
        self.assertEqual(
            expand("80,443,8000-8002"),
            [80, 443, 8000, 8001, 8002],
        )

    def test_sorted_output(self):
        # Caller wrote them out of order; we still return sorted.
        self.assertEqual(expand("9000,80,443"), [80, 443, 9000])

    def test_duplicates_collapsed(self):
        self.assertEqual(expand("80,80,80"), [80])

    def test_overlapping_ranges(self):
        self.assertEqual(expand("8000-8002,8001-8003"), [8000, 8001, 8002, 8003])

    def test_empty_string(self):
        self.assertEqual(expand(""), [])

    def test_port_zero(self):
        # 0 is a valid port number per IANA; we permit it.
        self.assertEqual(expand("0"), [0])

    def test_max_port(self):
        self.assertEqual(expand("65535"), [65535])

    def test_range_single_element(self):
        # lo == hi is a degenerate but legal range.
        self.assertEqual(expand("80-80"), [80])

    def test_whole_range_collapses(self):
        self.assertEqual(expand("80,80-80"), [80])


class ExpandUniqueTests(unittest.TestCase):
    def test_returns_set(self):
        self.assertIsInstance(expand_unique("80,443"), set)
        self.assertEqual(expand_unique("80,443"), {80, 443})

    def test_empty_returns_empty_set(self):
        self.assertEqual(expand_unique(""), set())


class ParseTokensTests(unittest.TestCase):
    def test_single(self):
        self.assertEqual(parse_tokens("80"), [80])

    def test_range_returns_tuple(self):
        self.assertEqual(parse_tokens("8000-8100"), [(8000, 8100)])

    def test_mixed(self):
        self.assertEqual(
            parse_tokens("80,443,8000-8100"),
            [80, 443, (8000, 8100)],
        )

    def test_empty_returns_empty_list(self):
        self.assertEqual(parse_tokens(""), [])


class ErrorCases(unittest.TestCase):
    def _expect(self, bad_spec):
        with self.assertRaises(PortRangeError):
            expand(bad_spec)

    def test_whitespace_rejected(self):
        self._expect("80, 443")

    def test_leading_zero_rejected(self):
        self._expect("080")

    def test_dangling_dash_start(self):
        self._expect("-80")

    def test_dangling_dash_end(self):
        self._expect("80-")

    def test_multiple_dashes(self):
        self._expect("8000-8010-8020")

    def test_swapped_bounds(self):
        self._expect("8100-8000")

    def test_out_of_range_high(self):
        self._expect("65536")

    def test_out_of_range_negative(self):
        # The '-' triggers the dangling-dash path before int parsing, but
        # the important thing is that it raises.
        self._expect("-1")

    def test_non_numeric(self):
        self._expect("abc")

    def test_empty_token_from_trailing_comma(self):
        self._expect("80,")

    def test_empty_token_from_leading_comma(self):
        self._expect(",80")

    def test_empty_token_double_comma(self):
        self._expect("80,,443")

    def test_non_string_input(self):
        with self.assertRaises(PortRangeError):
            expand(None)  # type: ignore[arg-type]
        with self.assertRaises(PortRangeError):
            expand(80)  # type: ignore[arg-type]

    def test_range_endpoint_out_of_range(self):
        self._expect("65535-65536")

    def test_range_endpoint_leading_zero(self):
        self._expect("080-082")


if __name__ == "__main__":
    unittest.main()
