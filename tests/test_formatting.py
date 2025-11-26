import math
import subprocess
import unittest
from pathlib import Path

import trimmed_average as ta


class FormattingTests(unittest.TestCase):
    def test_nan_output_when_trim_excludes_all(self):
        state = ta.TrimState(window_size=2, lower_abs=1, upper_abs=1)
        outputs = state.add_samples([1.0, 2.0])
        self.assertEqual(len(outputs), 1)
        index, avg = outputs[0]
        self.assertTrue(math.isnan(avg))
        self.assertTrue(ta.format_output(index, avg).endswith("NaN"))
        print("test_formatting.test_nan_output_when_trim_excludes_all passed")

    def test_cli_against_example(self):
        example_path = Path(__file__).resolve().parent.parent / "inputs" / "example-2.txt"
        with example_path.open("r", encoding="utf-8") as handle:
            result = subprocess.run(
                ["python3", "trimmed_average.py"],
                stdin=handle,
                text=True,
                capture_output=True,
                check=True,
            )
        output_lines = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertTrue(output_lines)
        self.assertTrue(all(len(line.split(":")) == 2 for line in output_lines))
        self.assertTrue(all(line.split(":")[0].strip().isdigit() for line in output_lines))
        print("test_formatting.test_cli_against_example passed")


if __name__ == "__main__":
    unittest.main()
