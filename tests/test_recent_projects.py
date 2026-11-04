import json

from appCommon.recent_projects import load_recent_project_paths


def write_recent_file(path, records):
    path.write_text(json.dumps(records), encoding="utf-8")


def test_returns_existing_projects_newest_first_and_deduped(tmp_path):
    first = tmp_path / "first.FlatPrj"
    second = tmp_path / "second.FlatPrj"
    first.write_text("project", encoding="utf-8")
    second.write_text("project", encoding="utf-8")

    recent_file = tmp_path / "recent_projects.json"
    write_recent_file(
        recent_file,
        [
            {"filename": str(first), "kind": "project"},
            {"filename": str(tmp_path / "missing.FlatPrj"), "kind": "project"},
            {"filename": str(tmp_path / "board.gbr"), "kind": "gerber"},
            {"filename": str(second), "kind": "project"},
            {"filename": str(first), "kind": "project"},
            "not-a-record",
        ],
    )

    assert load_recent_project_paths(recent_file) == [str(first), str(second)]


def test_honors_limit(tmp_path):
    first = tmp_path / "first.FlatPrj"
    second = tmp_path / "second.FlatPrj"
    first.write_text("project", encoding="utf-8")
    second.write_text("project", encoding="utf-8")

    recent_file = tmp_path / "recent_projects.json"
    write_recent_file(
        recent_file,
        [
            {"filename": str(first), "kind": "project"},
            {"filename": str(second), "kind": "project"},
        ],
    )

    assert load_recent_project_paths(recent_file, limit=1) == [str(first)]


def test_missing_file_returns_empty_list(tmp_path):
    assert load_recent_project_paths(tmp_path / "absent.json") == []


def test_malformed_json_returns_empty_list(tmp_path):
    recent_file = tmp_path / "recent_projects.json"
    recent_file.write_text("{not json", encoding="utf-8")

    assert load_recent_project_paths(recent_file) == []


def test_non_list_payload_returns_empty_list(tmp_path):
    recent_file = tmp_path / "recent_projects.json"
    write_recent_file(recent_file, {"filename": "x", "kind": "project"})

    assert load_recent_project_paths(recent_file) == []
