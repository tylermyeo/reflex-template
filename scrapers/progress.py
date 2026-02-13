"""
Progress indicators for scraper and selector discovery scripts.

Provides animated progress bars and spinners during waiting periods.
"""

import sys
import threading
import time
from contextlib import contextmanager
from typing import Iterator


def _use_progress() -> bool:
    """Check if progress indicators should be shown (TTY output)."""
    return sys.stdout.isatty()


def sleep_with_progress(seconds: float, desc: str = "Waiting") -> None:
    """Sleep with an animated progress bar."""
    if seconds <= 0:
        return
    if not _use_progress():
        time.sleep(seconds)
        return
    try:
        from tqdm import tqdm
        steps = max(1, int(seconds * 10))  # ~10 updates per second
        delay = seconds / steps
        for _ in tqdm(
            range(steps),
            desc=desc,
            total=steps,
            leave=False,
            bar_format="{desc}: {bar}| {elapsed}<{remaining}",
            ncols=60,
        ):
            time.sleep(delay)
    except ImportError:
        time.sleep(seconds)


@contextmanager
def spinner(desc: str = "Loading") -> Iterator[None]:
    """
    Context manager that shows a spinning indicator during execution.
    Usage:
        with spinner("Fetching page..."):
            do_something()
    """
    if not _use_progress():
        yield
        return

    chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    stop = threading.Event()
    done = [False]

    def spin() -> None:
        i = 0
        while not stop.is_set():
            sys.stdout.write(f"\r  {chars[i % len(chars)]} {desc}   ")
            sys.stdout.flush()
            i += 1
            stop.wait(0.08)

    t = threading.Thread(target=spin, daemon=True)
    t.start()
    try:
        yield
    finally:
        stop.set()
        t.join(timeout=0.5)
        sys.stdout.write("\r" + " " * (len(desc) + 8) + "\r")
        sys.stdout.flush()
