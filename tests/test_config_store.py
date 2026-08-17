import json

from src.config_store import DEFAULT_CATEGORIES, load_config, normalize_config, save_config


def test_normalize_config_repairs_missing_fields():
    config = normalize_config({"buttons": [{"label": "  Test  ", "category": "Custom", "command": "cmd:echo hi"}, "bad entry"]})
    assert config["buttons"] == [{"label": "Test", "command": "cmd:echo hi", "icon": "", "category": "Custom", "enabled": True}]
    assert "Custom" in config["categories"]


def test_load_config_falls_back_to_bundled(tmp_path):
    bundled = tmp_path / "bundled.json"
    bundled.write_text(json.dumps({"categories": ["One"], "buttons": []}), encoding="utf-8")
    loaded = load_config(tmp_path / "missing.json", bundled)
    assert loaded["categories"] == ["One"]


def test_load_config_uses_defaults_when_files_are_invalid(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text("{not-json", encoding="utf-8")
    loaded = load_config(broken, None)
    assert loaded["categories"] == DEFAULT_CATEGORIES
    assert loaded["buttons"]


def test_save_config_writes_normalized_json(tmp_path):
    target = tmp_path / "nested" / "config.json"
    saved = save_config({"categories": ["Apps"], "buttons": [{"label": "X", "category": "Apps"}]}, target)
    assert saved == target
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["buttons"][0]["command"] == ""
    assert payload["buttons"][0]["enabled"] is True
