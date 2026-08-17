import json

import pytest

from src.config_store import (
    DEFAULT_CATEGORIES,
    create_profile,
    delete_profile,
    export_profile,
    get_active_deck,
    import_profile,
    load_config,
    normalize_config,
    rename_profile,
    save_config,
)


def test_normalize_config_migrates_original_single_deck_format():
    config = normalize_config(
        {
            "categories": ["Applications"],
            "buttons": [
                {
                    "label": " Test ",
                    "category": "Custom",
                    "command": "cmd:echo hi",
                }
            ],
        }
    )
    assert config["active_profile"] == "Default"
    assert "Default" in config["profiles"]
    assert get_active_deck(config)["buttons"] == [
        {
            "label": "Test",
            "command": "cmd:echo hi",
            "icon": "",
            "category": "Custom",
            "enabled": True,
        }
    ]
    assert "Custom" in get_active_deck(config)["categories"]


def test_load_config_falls_back_to_bundled(tmp_path):
    bundled = tmp_path / "bundled.json"
    bundled.write_text(
        json.dumps(
            {
                "active_profile": "One",
                "profiles": {"One": {"categories": ["One"], "buttons": []}},
            }
        ),
        encoding="utf-8",
    )
    loaded = load_config(tmp_path / "missing.json", bundled)
    assert loaded["active_profile"] == "One"
    assert get_active_deck(loaded)["categories"] == ["One"]


def test_load_config_uses_defaults_when_files_are_invalid(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text("{not-json", encoding="utf-8")
    loaded = load_config(broken, None)
    assert get_active_deck(loaded)["categories"] == DEFAULT_CATEGORIES
    assert get_active_deck(loaded)["buttons"]


def test_save_config_writes_normalized_json(tmp_path):
    target = tmp_path / "nested" / "config.json"
    config = normalize_config(
        {
            "active_profile": "Work",
            "profiles": {
                "Work": {
                    "categories": ["Apps"],
                    "buttons": [{"label": "X", "category": "Apps"}],
                }
            },
        }
    )
    saved = save_config(config, target)
    assert saved == target
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["profiles"]["Work"]["buttons"][0]["command"] == ""
    assert payload["obs"]["port"] == 4455


def test_profile_create_rename_delete():
    config = normalize_config({})
    created = create_profile(config, "Gaming")
    assert created == "Gaming"
    assert config["active_profile"] == "Gaming"
    assert get_active_deck(config)["buttons"] == []

    renamed = rename_profile(config, "Gaming", "Streaming")
    assert renamed == "Streaming"
    assert config["active_profile"] == "Streaming"

    delete_profile(config, "Streaming")
    assert config["active_profile"] == "Default"

    with pytest.raises(ValueError):
        delete_profile(config, "Default")


def test_export_and_import_profile_round_trip(tmp_path):
    config = normalize_config({})
    create_profile(config, "Gaming")
    get_active_deck(config)["buttons"].append(
        {
            "label": "OBS Gaming",
            "command": "obs_scene:Gaming",
            "icon": "",
            "category": "Video",
            "enabled": True,
        }
    )

    exported = tmp_path / "gaming.streamflow.json"
    export_profile(config, "Gaming", exported)

    other = normalize_config({})
    imported_name = import_profile(other, exported)
    assert imported_name == "Gaming"
    assert other["active_profile"] == "Gaming"
    assert get_active_deck(other)["buttons"][0]["command"] == "obs_scene:Gaming"
