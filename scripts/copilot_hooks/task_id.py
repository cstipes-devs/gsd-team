#!/usr/bin/env python3
"""Print the verification-sentinel id for a task line.

Agents call this to learn where to write their sentinel, so that the id they
use matches the one the gate will look for.

    $ python3 scripts/copilot_hooks/task_id.py \
        '- [ ] [go] Add retry | internal/retry.go | retries 3x. Run: go test ./...'
    a1b2c3d4e5f6

With --path and a spec slug, print the full sentinel path instead:

    $ python3 scripts/copilot_hooks/task_id.py --path --slug my-feature '<task line>'
    /Users/you/.gsd-team/logs/verified/my-feature/task-a1b2c3d4e5f6.verified
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gsd_hook_lib as lib  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("task_line", help="the full task line, quoted")
    ap.add_argument("--path", action="store_true",
                    help="print the full sentinel path")
    ap.add_argument("--slug", default="", help="spec slug, used with --path")
    args = ap.parse_args()

    line = args.task_line
    m = lib.TASK_LINE_RE.match(line)
    body = m.group("body").strip() if m else line.strip()

    tid = lib.task_id(body)

    if args.path:
        if not args.slug:
            ap.error("--path requires --slug")
        print(lib.sentinel_path(args.slug, tid))
    else:
        print(tid)


if __name__ == "__main__":
    main()
