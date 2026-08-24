# Version 0.3 failure and recovery exercises

These exercises are deliberately local and should not require a real API call unless explicitly
noted. Use a copy of the example script and a temporary output directory when experimenting.

## Validate an existing episode

```bash
uv run commute-podcast validate episodes/pilot-episode.mp3
```

This uses `ffprobe` to confirm the file is an MP3 with an audio stream and reports technical
metadata. Loudness measurement remains a separate `ffmpeg ebur128` operation.

## Exercise atomic synthesis

```bash
uv run pytest tests/test_resilience.py -k atomic
```

Temporary names begin with `.` and end in `.tmp`; they must not remain after synthesis.

## Exercise retry behavior

```bash
uv run pytest tests/test_resilience.py -k retry
```

The test simulates two connection failures followed by success. Non-transient errors are raised
immediately, and the maximum attempt count prevents an infinite retry loop.

## Exercise resume and invalidation

1. Start a multi-chunk real generation only when you accept the API cost.
2. Interrupt it after at least one chunk completes.
3. Run the same command again and look for `chunk_reused` in the logs.
4. Replace one part with an empty or invalid file and run again.
5. Look for `chunk_invalidated` and confirm that the part is regenerated.

The manifest records failure state when the process catches an exception. A hard process kill can
still occur before that manifest write; durable incremental state is later work.

## Exercise the paid integration test

The normal suite skips the real API test. Run it only with a valid key and explicit consent:

```bash
RUN_REAL_API_TESTS=1 uv run pytest tests/test_integration.py -m integration
```

This creates one short episode and incurs provider cost.
