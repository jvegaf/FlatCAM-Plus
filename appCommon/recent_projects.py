import json
import os


def load_recent_project_paths(
    recent_projects_file, limit=None, path_exists=os.path.exists
):
    """Return existing project paths from a recent projects file, newest first.

    Records must be dictionaries with kind "project" and a filename. Duplicate
    paths are removed and paths that no longer exist are ignored. When limit is
    a positive integer, at most that many paths are returned.
    """
    try:
        with open(recent_projects_file, "r", encoding="utf-8") as handle:
            records = json.load(handle)
    except OSError, json.JSONDecodeError, TypeError:
        return []

    if not isinstance(records, list):
        return []

    paths = []
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        if str(record.get("kind", "")).lower() != "project":
            continue
        filename = record.get("filename")
        if not isinstance(filename, str) or not filename:
            continue
        if filename in seen:
            continue
        if not path_exists(filename):
            continue
        seen.add(filename)
        paths.append(filename)
        if isinstance(limit, int) and limit > 0 and len(paths) >= limit:
            break
    return paths
