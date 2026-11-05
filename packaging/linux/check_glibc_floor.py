"""Refuse a bundle that needs a newer glibc than the oldest distribution we target.

glibc is forward-compatible only: a bundle built against the newest runtime starts on that machine
and fails on older ones. The floor is therefore whatever the build host offers, and it drifts
silently the moment somebody builds on a newer runner. This compares the bundle's own symbol
requirements against a declared floor and fails loudly when it moves.

Usage: check_glibc_floor.py <bundle-dir> [expected-floor]

The expected floor defaults to the environmental contract of the packaging pipeline: 2.28, the
manylinux tag every native wheel in uv.lock requires and the glibc of RHEL/Alma/Rocky 9.
"""

import re
import subprocess
import sys
from pathlib import Path

EXPECTED_FLOOR = "2.28"
SYMBOL = re.compile(r"GLIBC_(\d+)\.(\d+)")
SHARED_OBJECT = re.compile(r"\.so(\.\d+)*$")


def version_tuple(version):
    major, minor = version.split(".")[:2]
    return (int(major), int(minor))


def max_glibc_version(objdump_output):
    """The highest GLIBC_x.y token in `objdump -T` output, or None when there is none."""
    found = [match.groups() for match in SYMBOL.finditer(objdump_output)]
    if not found:
        return None
    major, minor = max(found, key=lambda pair: (int(pair[0]), int(pair[1])))
    return "{0}.{1}".format(major, minor)


def bundle_libraries(bundle_dir):
    return sorted(
        path
        for path in Path(bundle_dir).rglob("*")
        if path.is_file() and SHARED_OBJECT.search(path.name)
    )


def symbols_of(path):
    finished = subprocess.run(
        ["objdump", "-T", str(path)], capture_output=True, text=True, check=False
    )
    return finished.stdout


def main(argv):
    if not 2 <= len(argv) <= 3:
        print("usage: check_glibc_floor.py <bundle-dir> [expected-floor]", file=sys.stderr)
        return 2
    bundle_dir = Path(argv[1])
    expected = argv[2] if len(argv) == 3 else EXPECTED_FLOOR

    libraries = bundle_libraries(bundle_dir)
    if not libraries:
        print("no shared objects under {0}".format(bundle_dir), file=sys.stderr)
        return 1

    highest = None
    worst = None
    for library in libraries:
        candidate = max_glibc_version(symbols_of(library))
        if candidate and (highest is None or version_tuple(candidate) > version_tuple(highest)):
            highest, worst = candidate, library
    if highest is None:
        print("no glibc symbol references found; is objdump installed?", file=sys.stderr)
        return 1

    if version_tuple(highest) > version_tuple(expected):
        print(
            "glibc floor drifted: {0} needs GLIBC_{1}, the pipeline promises {2}".format(
                worst, highest, expected
            ),
            file=sys.stderr,
        )
        return 1

    print("glibc floor ok: highest reference is GLIBC_{0} (promised {1})".format(highest, expected))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
