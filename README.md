# Moving Trimmed Average

This repository implements the moving trimmed average program described in `exercise.md`.
It decodes the base64-formatted instruction stream, executes configuration and sample
segments, and prints each calculated trimmed average in the required format.

## Usage

```
python3 trimmed_average.py < inputs/example-1.txt
python3 trimmed_average.py < inputs/example-2.txt
python3 trimmed_average.py < inputs/example-3.txt
```

## Testing

There is no single test runner script. Each test file can be run on its own so the
commands stay obvious and human-sized:

```
python3 -m unittest tests.test_basic_flow
python3 -m unittest tests.test_trimmed_average
python3 -m unittest tests.test_stream_coverage
python3 -m unittest tests.test_formatting
```
