import math
import unittest

import trimmed_average as ta


class BasicFlowTests(unittest.TestCase):
    def test_handles_small_window_and_reset(self):
        # Start with a very small window to mirror how a junior dev might poke at the code.
        state = ta.TrimState()
        state.set_window_size(2)

        # Feed a couple of samples and make sure we get the first average back.
        outputs = state.add_samples([1.0, 3.0])
        self.assertEqual(outputs, [(2, 2.0)])

        # Flip a trim setting to force a reset and see that the index restarts.
        state.set_lower_abs(1)
        outputs = state.add_samples([4.0, 6.0])
        index, avg = outputs[0]
        self.assertEqual(index, 2)
        # After trimming away the lowest of the two samples, only 6.0 is left.
        self.assertTrue(math.isclose(avg, 6.0))
        print("test_basic_flow.test_handles_small_window_and_reset passed")

    def test_combines_abs_and_prop_trims(self):
        # Check the combined trim path with numbers that are easy to eyeball.
        state = ta.TrimState(window_size=4, lower_abs=1, upper_prop=25)
        outputs = state.add_samples([10.0, 20.0, 30.0, 40.0])
        self.assertEqual(len(outputs), 1)
        _, avg = outputs[0]
        # lower_abs trims 1, upper_prop trims ceil(25% of 4) = 1, leaving 20 and 30 => average 25
        self.assertTrue(math.isclose(avg, 25.0))
        print("test_basic_flow.test_combines_abs_and_prop_trims passed")


if __name__ == "__main__":
    unittest.main()
