"""Every live ``app.options["geometry_*"]`` read must be defined in the shipped defaults.

``app.options`` is a plain ``LoudDict`` populated from ``AppDefaults.factory_defaults``, so a
read of a key that was never defined raises ``KeyError`` at the first use of the owning code
path. ``appParsers/ParseHPGL2.py`` built its whole ``default_data`` dictionary that way: twelve
``geometry_*`` keys were read but never shipped, so constructing the parser failed before a
single line of HPGL2 could be parsed.

The scan is deliberately name-agnostic: it collects the option reads from the source instead
of listing the known keys, so a new read added anywhere in the tree is covered without
touching this file. Commented-out reads are not live code and are ignored.
"""

import ast
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULTS_PATH = os.path.join(REPO_ROOT, "flatcam_plus", "defaults.py")

# Directories that either are not project source or hold copies of it (the candidate views are
# generated snapshots kept under ``.git``). Scanning them would report reads the shipped app
# never executes and would make the walk unbounded.
SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules", "candidate-views"}

OPTION_READ = re.compile(r"""app\.options\[\s*(['"])(geometry_[A-Za-z0-9_]+)\1\s*\]""")

# Built from parts so the synthetic sample below is not itself collected as a live read of the
# option name it is testing.
SYNTHETIC_READ = "%s.options[%r]"


def _python_files():
    """Yield every project Python file outside the skipped directories."""
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                yield os.path.join(dirpath, filename)


def _live_geometry_reads(path):
    """Return ``{option_name: [line numbers]}`` for the live reads in one file."""
    reads = {}
    with open(path, encoding="utf-8", errors="replace") as handle:
        for number, line in enumerate(handle, start=1):
            if line.strip().startswith("#"):
                continue
            for match in OPTION_READ.finditer(line):
                reads.setdefault(match.group(2), []).append(number)
    return reads


def _scanned_reads():
    reads = {}
    for path in _python_files():
        for name, lines in _live_geometry_reads(path).items():
            reads.setdefault(name, []).extend((path, line) for line in lines)
    return reads


def _factory_default_keys():
    """The option names declared in the ``factory_defaults`` dictionary literal."""
    with open(DEFAULTS_PATH, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=DEFAULTS_PATH)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if "factory_defaults" not in targets or not isinstance(node.value, ast.Dict):
            continue
        return {
            key.value
            for key in node.value.keys
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
        }
    raise AssertionError("flatcam_plus/defaults.py no longer declares factory_defaults")


def test_the_scan_actually_finds_option_reads():
    # A scan that silently walked nothing would make the coverage assertion vacuous.
    reads = _scanned_reads()
    assert "geometry_feedrate" in reads
    assert len(reads) > 10


def test_the_scan_stays_inside_the_project_sources():
    # ``.git`` holds the generated candidate views, which are copies of these same files.
    sites = [path for where in _scanned_reads().values() for path, _ in where]
    assert sites
    for path in sites:
        relative = os.path.relpath(path, REPO_ROOT)
        assert not relative.startswith("..")
        assert not set(relative.split(os.sep)) & SKIP_DIRS


def test_defaults_declare_a_large_option_set():
    assert len(_factory_default_keys()) > 500


def test_only_live_reads_are_collected(tmp_path):
    source = tmp_path / "sample.py"
    source.write_text(
        "def build(app):\n"
        "    live = " + SYNTHETIC_READ % ("app", "geometry_live_key") + "\n"
        "    also = " + SYNTHETIC_READ % ("app", "geometry_also_live") + "\n"
        "    # dead = " + SYNTHETIC_READ % ("app", "geometry_commented_key") + "\n"
        "    #\n"
        "    #    nested = " + SYNTHETIC_READ % ("app", "geometry_nested_comment") + "\n",
        encoding="utf-8",
    )
    assert sorted(_live_geometry_reads(str(source))) == ["geometry_also_live", "geometry_live_key"]


def test_every_live_geometry_option_is_defined_in_defaults():
    defined = _factory_default_keys()
    missing = {name: where for name, where in _scanned_reads().items() if name not in defined}
    assert missing == {}, "\n".join(
        "%s read at %s" % (name, ", ".join("%s:%d" % site for site in sites))
        for name, sites in sorted(missing.items())
    )
