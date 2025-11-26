import base64
import math
import struct
import subprocess
import sys
import unittest

import trimmed_average as ta


def build_stream_with_opcode(opcode: int, payload: bytes = b"") -> bytes:
    return bytes([opcode]) + payload


class StreamCoverageTests(unittest.TestCase):
    def test_truncated_stream_raises_value_error(self):
        # Missing the payload 
        raw = build_stream_with_opcode(0x01)
        with self.assertRaises(ValueError):
            ta.parse_stream(raw, ta.TrimState())
        print("test_stream_coverage.test_truncated_stream_raises_value_error passed")

    def test_large_window_and_trim_combo(self):
        # Build a stream that mixes absolute and proportional trims 
        payload = b"".join(
            [
                build_stream_with_opcode(0x05, (6).to_bytes(4, "big")),  # window size 6
                build_stream_with_opcode(0x01, bytes([1])),  # lower abs
                build_stream_with_opcode(0x03, bytes([10])),  # lower prop
                build_stream_with_opcode(0x02, bytes([1])),  # upper abs
                build_stream_with_opcode(0x04, bytes([10])),  # upper prop
                build_stream_with_opcode(
                    0x10,
                    bytes([6]) + struct.pack(">6d", *[10.0, 20.0, 30.0, 40.0, 50.0, 60.0]),
                ),
            ]
        )
        outputs = ta.parse_stream(payload, ta.TrimState())
        self.assertEqual(len(outputs), 1)
        # Trim drops the two smallest and two largest values => average of 30 and 40
        index, avg_text = outputs[0].split(":")
        self.assertEqual(index.strip(), "6")
        self.assertTrue(math.isclose(float(avg_text.strip()), 35.0, rel_tol=1e-9))
        print("test_stream_coverage.test_large_window_and_trim_combo passed")

    def test_main_via_subprocess_reports_nan_on_over_trim(self):
        # Feed a stream that over-trims. returns NaN
        raw_stream = b"".join(
            [
                build_stream_with_opcode(0x05, (2).to_bytes(4, "big")),
                build_stream_with_opcode(0x01, bytes([2])),  # trims exceed window
                build_stream_with_opcode(0x10, bytes([2]) + struct.pack(">2d", 1.0, 2.0)),
            ]
        )
        encoded = base64.b64encode(raw_stream).decode("ascii")
        process = subprocess.run(
            [sys.executable, "trimmed_average.py"],
            input=encoded,
            text=True,
            capture_output=True,
            check=True,
        )
        lines = [line for line in process.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].endswith("NaN"))
        print("test_stream_coverage.test_main_via_subprocess_reports_nan_on_over_trim passed")


if __name__ == "__main__":
    unittest.main()
