import math
import struct
import unittest
from pathlib import Path

import trimmed_average as ta


def build_raw_stream(*parts: bytes) -> bytes:
    return b"".join(parts)


def encode_samples(samples):
    return struct.pack(f">{len(samples)}d", *samples)


class DecodeInputLinesTests(unittest.TestCase):
    def test_decode_input_lines_strips_comments_and_padding(self):
        lines = [
            "# comment should go",  # ignored
            " TQ",  # base64 for 'M' with padding implied
            "VA==  ",  # base64 for 'T' with padding included
            "  \n",  # blank line
        ]
        decoded = ta.decode_input_lines(lines)
        self.assertEqual(decoded, b"MT")


class TrimmedAverageTests(unittest.TestCase):
    def test_trimmed_average_handles_absolute_and_proportional_trimming(self):
        state = ta.TrimState(window_size=10, lower_abs=1, upper_prop=10)
        samples = [float(i) for i in range(10)]
        outputs = state.add_samples(samples)
        self.assertEqual(len(outputs), 1)
        index, avg = outputs[0]
        self.assertEqual(index, 10)
        # lower trim = 1, upper trim = ceil(10%*10)=1 => drop 0 and 9 => mean of 1..8 = 4.5
        self.assertTrue(math.isclose(avg, 4.5))

    def test_parse_stream_reset_on_parameter_change(self):
        # window size 3, lower_abs changes from default 0 to 1 and implies reset
        raw = build_raw_stream(
            b"\x05" + (3).to_bytes(4, "big"),  # set window size 3
            b"\x10\x03" + encode_samples([1.0, 2.0, 3.0]),
            b"\x01\x01",  # set lower abs trim to 1 (reset)
            b"\x10\x03" + encode_samples([4.0, 5.0, 6.0]),
        )
        outputs = ta.parse_stream(raw, ta.TrimState())
        # first three samples produce one output without trimming
        self.assertTrue(outputs[0].endswith("2.000"))
        # after reset, index restarts at 3 for the second window
        self.assertTrue(outputs[1].startswith("      3"))

    def test_parse_stream_matches_example_one(self):
        example_path = Path(__file__).resolve().parent.parent / "inputs" / "example-1.txt"
        with example_path.open("r", encoding="utf-8") as f:
            raw = ta.decode_input_lines(f)
        outputs = ta.parse_stream(raw, ta.TrimState())
        self.assertEqual(
            outputs,
            [
                "      5: 0.250",
                "      6: 0.350",
                "      7: 0.450",
                "      8: 0.550",
            ],
        )


if __name__ == "__main__":
    unittest.main()
