"""Simple command-line tool for computing moving trimmed averages."""
from __future__ import annotations

import base64
import bisect
import math
import struct
import sys
from collections import deque
from typing import Iterable, List, Sequence, Tuple


# Opcodes are kept near the top so they are easy to eyeball while reading the spec.
RESET = 0x00
SET_LOWER_ABS = 0x01
SET_UPPER_ABS = 0x02
SET_LOWER_PROP = 0x03
SET_UPPER_PROP = 0x04
SET_WINDOW_SIZE = 0x05
ADD_SAMPLES = 0x10


class TrimState:
    """Holds the mutable state for the rolling calculation."""

    def __init__(self, window_size: int = 0, lower_abs: int = 0, upper_abs: int = 0,
                 lower_prop: int = 0, upper_prop: int = 0) -> None:
        # Window and trim configuration.
        self.window_size = window_size
        self.lower_abs = lower_abs
        self.upper_abs = upper_abs
        self.lower_prop = lower_prop
        self.upper_prop = upper_prop

        # Data that shifts as new samples arrive.
        self.samples: deque[float] = deque()
        self.sorted_samples: List[float] = []
        self.total_sum: float = 0.0
        self.samples_seen: int = 0

    def reset_samples(self) -> None:
        # This is called both by explicit RESET and whenever any trim setting changes.
        self.samples.clear()
        self.sorted_samples.clear()
        self.total_sum = 0.0
        self.samples_seen = 0

    def set_lower_abs(self, value: int) -> None:
        if value != self.lower_abs:
            self.lower_abs = value
            self.reset_samples()

    def set_upper_abs(self, value: int) -> None:
        if value != self.upper_abs:
            self.upper_abs = value
            self.reset_samples()

    def set_lower_prop(self, value: int) -> None:
        if value != self.lower_prop:
            self.lower_prop = value
            self.reset_samples()

    def set_upper_prop(self, value: int) -> None:
        if value != self.upper_prop:
            self.upper_prop = value
            self.reset_samples()

    def set_window_size(self, value: int) -> None:
        if value != self.window_size:
            self.window_size = value
            self.reset_samples()

    def add_samples(self, samples: Sequence[float]) -> List[Tuple[int, float]]:
        """Insert samples, trimming any overflow, and return outputs that completed windows."""
        outputs: List[Tuple[int, float]] = []
        for sample in samples:
            self.samples_seen += 1
            self.samples.append(sample)
            bisect.insort(self.sorted_samples, sample)
            self.total_sum += sample

            # If the window is too big, pop from both trackers.
            if self.window_size > 0 and len(self.samples) > self.window_size:
                removed = self.samples.popleft()
                self.total_sum -= removed
                idx = bisect.bisect_left(self.sorted_samples, removed)
                del self.sorted_samples[idx]

            # Only compute when the window is fully populated.
            if self.window_size > 0 and len(self.samples) == self.window_size:
                outputs.append((self.samples_seen, self.compute_trimmed_average()))
        return outputs

    def compute_trimmed_average(self) -> float:
        # Guard against uninitialized state.
        if self.window_size == 0 or len(self.sorted_samples) < self.window_size:
            return math.nan

        n = self.window_size
        # The assignment says to pick the bigger trim between absolute and proportional.
        low_trim = max(self.lower_abs, math.ceil(self.lower_prop * n / 100))
        high_trim = max(self.upper_abs, math.ceil(self.upper_prop * n / 100))

        # If everything gets trimmed away, we return NaN so the caller can print it.
        if low_trim + high_trim >= n:
            return math.nan

        trimmed_sum = self.total_sum
        if low_trim:
            trimmed_sum -= sum(self.sorted_samples[:low_trim])
        if high_trim:
            trimmed_sum -= sum(self.sorted_samples[-high_trim:])

        trimmed_count = n - low_trim - high_trim
        return trimmed_sum / trimmed_count


def decode_input_lines(lines: Iterable[str]) -> bytes:
    """Turn the text input into one continuous bytes object."""
    chunks: List[bytes] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            # Skip comments and blank lines to match the exercise format.
            continue

        padding_len = (-len(stripped)) % 4
        padded = stripped + ("=" * padding_len)
        chunks.append(base64.b64decode(padded))
    return b"".join(chunks)


def parse_stream(raw: bytes, state: TrimState) -> List[str]:
    """Walk over the raw bytes and collect formatted outputs."""
    outputs: List[str] = []
    idx = 0
    length = len(raw)

    while idx < length:
        code = raw[idx]
        idx += 1

        if code == RESET:
            state.reset_samples()
        elif code == SET_LOWER_ABS:
            if idx >= length:
                raise ValueError("Unexpected end of stream while reading SLAT value")
            value = raw[idx]
            idx += 1
            state.set_lower_abs(value)
        elif code == SET_UPPER_ABS:
            if idx >= length:
                raise ValueError("Unexpected end of stream while reading SUAT value")
            value = raw[idx]
            idx += 1
            state.set_upper_abs(value)
        elif code == SET_LOWER_PROP:
            if idx >= length:
                raise ValueError("Unexpected end of stream while reading SLPT value")
            value = raw[idx]
            idx += 1
            state.set_lower_prop(value)
        elif code == SET_UPPER_PROP:
            if idx >= length:
                raise ValueError("Unexpected end of stream while reading SUPT value")
            value = raw[idx]
            idx += 1
            state.set_upper_prop(value)
        elif code == SET_WINDOW_SIZE:
            if idx + 4 > length:
                raise ValueError("Unexpected end of stream while reading window size")
            value = int.from_bytes(raw[idx:idx + 4], "big")
            idx += 4
            state.set_window_size(value)
        elif code == ADD_SAMPLES:
            if idx >= length:
                raise ValueError("Unexpected end of stream while reading sample count")
            count = raw[idx]
            idx += 1
            bytes_needed = count * 8
            if idx + bytes_needed > length:
                raise ValueError("Unexpected end of stream while reading samples")
            sample_bytes = raw[idx:idx + bytes_needed]
            idx += bytes_needed
            samples = list(struct.unpack(f">{count}d", sample_bytes))
            for sample_index, value in state.add_samples(samples):
                outputs.append(format_output(sample_index, value))
        else:
            raise ValueError(f"Unknown instruction code: {code:#04x}")

    return outputs


def format_output(index: int, avg: float) -> str:
    # Using NaN text keeps downstream consumers from mistaking it for a real number.
    if math.isnan(avg):
        value_text = "NaN"
    else:
        value_text = f"{avg:.3f}"
    return f"{index:7d}: {value_text}"


def main() -> None:
    raw_stream = decode_input_lines(sys.stdin)
    state = TrimState()
    for line in parse_stream(raw_stream, state):
        print(line)


if __name__ == "__main__":
    main()
