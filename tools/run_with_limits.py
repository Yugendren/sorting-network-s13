#!/usr/bin/env python3
"""Apply a kernel CPU limit, then replace this process with a command."""

from __future__ import annotations

import argparse
import os
import resource


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpu-seconds", type=int, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.command:
        parser.error("a command is required")
    resource.setrlimit(resource.RLIMIT_CPU, (args.cpu_seconds, args.cpu_seconds + 5))
    os.execvpe(args.command[0], args.command, os.environ)


if __name__ == "__main__":
    main()
