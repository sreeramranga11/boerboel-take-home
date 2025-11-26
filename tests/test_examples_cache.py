import subprocess
import sys
import unittest
from pathlib import Path

import trimmed_average as ta


class ExampleCacheTests(unittest.TestCase):
    def run_example_and_collect(self, name: str):
        input_path = Path(__file__).resolve().parent.parent / "inputs" / name
        output_path = Path(__file__).resolve().parent.parent / "outputs" / f"{Path(name).stem}.out"
        if output_path.exists():
            output_path.unlink()

        with input_path.open("r", encoding="utf-8") as handle:
            process = subprocess.run(
                [sys.executable, "trimmed_average.py"],
                stdin=handle,
                text=True,
                capture_output=True,
                check=True,
            )

        stdout_lines = [line for line in process.stdout.splitlines() if line.strip()]
        self.assertTrue(output_path.exists(), "expected CLI to cache outputs")
        cached_lines = [line for line in output_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return stdout_lines, cached_lines

    def build_expected_lines(self, name: str):
        input_path = Path(__file__).resolve().parent.parent / "inputs" / name
        with input_path.open("r", encoding="utf-8") as handle:
            raw = ta.decode_input_lines(handle)
        return ta.parse_stream(raw, ta.TrimState())

    def test_example_two_matches_expected_and_caches(self):
        stdout_lines, cached_lines = self.run_example_and_collect("example-2.txt")
        expected_lines = self.build_expected_lines("example-2.txt")
        self.assertEqual(stdout_lines, expected_lines)
        self.assertEqual(cached_lines, expected_lines)
        print("test_examples_cache.test_example_two_matches_expected_and_caches passed")

    def test_example_three_matches_expected_and_caches(self):
        stdout_lines, cached_lines = self.run_example_and_collect("example-3.txt")
        expected_lines = self.build_expected_lines("example-3.txt")
        self.assertGreater(len(expected_lines), 10)
        self.assertEqual(stdout_lines[:5], expected_lines[:5])
        self.assertEqual(stdout_lines[-5:], expected_lines[-5:])
        self.assertEqual(cached_lines, expected_lines)
        print("test_examples_cache.test_example_three_matches_expected_and_caches passed")


if __name__ == "__main__":
    unittest.main()
