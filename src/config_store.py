from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path
from typing import Any

APP_DIR_NAME = ".streamflow"
CONFIG_FILE_NAME = "config.json"
DEFAULT_PROFILE_NAME = "Default"
DEFAULT_CATEGORIES = ["Applications", "Audio", "Video", "Messages", "More"]
DEFAULT_DECK: dict[str, Any] = {
    "categories": DEFAULT_CATEGORIES,
    "buttons": [
        {"label": "Open Browser", "command": "url:https://www.google.com", "icon": "", "category": "Applications", "enabled": True},
        {"label": "Mute Audio", "command": "mute", "icon": "", "category": "Audio", "enabled": True},
        {"label": "Volume +", "command": "volume_up", "icon": "", "category": "Audio", "enabled": True},
        {"label": "Volume -", "command": "volume_down", "icon": "", "category": "Audio", "enabled": True},
    ],
}
DEFAULT_OBS_SETTINGS = {"host": "127.0.0.1", "port": 4455, "password": ""}
DEFAULT_CONFIG: dict[str, Any] = {
    "active_profile": DEFAULT_PROFILE_NAME,
    "profiles": {DEFAULT_PROFILE_NAME: DEFAULT_DECK},
    "obs": DEFAULT_OBS_SETTINGS,
}


def get_user_config_path() -> Path:
    override = os.getenv("STREAMFLOW_CONFIG")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / APP_DIR_NAME / CONFIG_FILE_NAME


def normalize_deck(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}

    raw_categories = raw.get("categories", [])
    categories: list[str] = []
    if isinstance(raw_categories, list):
        for item in raw_categories:
            category = str(item).strip()
            if category and category not in categories:
                categories.append(category)
    if not categories:
        categories = list(DEFAULT_CATEGORIES)

    raw_buttons = raw.get("buttons")
    if raw_buttons is None:
        raw_buttons = copy.deepcopy(DEFAULT_DECK["buttons"])

    buttons: list[dict[str, Any]] = []
    if isinstance(raw_buttons, list):
        for item in raw_buttons:
            if not isinstance(item, dict):
                continue
            label = str(item.get("label", "Button")).strip() or "Button"
            category = str(item.get("category", "More")).strip() or "More"
            command = str(item.get("command", "")).strip()
            icon = str(item.get("icon", "")).strip()
            enabled = bool(item.get("enabled", True))
            if category not in categories:
                categories.append(category)
            buttons.append(
                {
                    "label": label,
                    "command": command,
                    "icon": icon,
                    "category": category,
                    "enabled": enabled,
                }
            )
    return {"categories": categories, "buttons": buttons}


def normalize_obs_settings(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}
    host = str(raw.get("host", DEFAULT_OBS_SETTINGS["host"])).strip() or DEFAULT_OBS_SETTINGS["host"]
    try:
        port = int(raw.get("port", DEFAULT_OBS_SETTINGS["port"]))
    except (TypeError, ValueError):
        port = DEFAULT_OBS_SETTINGS["port"]
    if not 1 <= port <= 65535:
        port = DEFAULT_OBS_SETTINGS["port"]
    password = str(raw.get("password", ""))
    return {"host": host, "port": port, "password": password}


def normalize_config(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}

    profiles: dict[str, dict[str, Any]] = {}
    raw_profiles = raw.get("profiles")
    if isinstance(raw_profiles, dict):
        for raw_name, raw_deck in raw_profiles.items():
            name = str(raw_name).strip()
            if name and name not in profiles:
                profiles[name] = normalize_deck(raw_deck)

    # Migrate the original single-deck format automatically.
    if not profiles:
        legacy = {}
        if "categories" in raw:
            legacy["categories"] = raw.get("categories")
        if "buttons" in raw:
            legacy["buttons"] = raw.get("buttons")
        profiles[DEFAULT_PROFILE_NAME] = normalize_deck(legacy)

    requested_active = str(raw.get("active_profile", "")).strip()
    active_profile = requested_active if requested_active in profiles else next(iter(profiles))

    return {
        "active_profile": active_profile,
        "profiles": profiles,
        "obs": normalize_obs_settings(raw.get("obs")),
    }


def get_active_deck(config: dict[str, Any]) -> dict[str, Any]:
    active = config["active_profile"]
    return config["profiles"][active]


def unique_profile_name(config: dict[str, Any], desired: str) -> str:
    base = desired.strip() or "Profile"
    if base not in config["profiles"]:
        return base
    counter = 2
    while f"{base} {counter}" in config["profiles"]:
        counter += 1
    return f"{base} {counter}"


def create_profile(config: dict[str, Any], name: str, source_name: str | None = None) -> str:
    name = unique_profile_name(config, name)
    if source_name and source_name in config["profiles"]:
        deck = copy.deepcopy(config["profiles"][source_name])
    else:
        deck = {"categories": list(DEFAULT_CATEGORIES), "buttons": []}
    config["profiles"][name] = normalize_deck(deck)
    config["active_profile"] = name
    return name


def rename_profile(config: dict[str, Any], old_name: str, new_name: str) -> str:
    if old_name not in config["profiles"]:
        raise KeyError(old_name)
    cleaned = new_name.strip()
    if not cleaned:
        raise ValueError("Profile name cannot be empty.")
    if cleaned != old_name and cleaned in config["profiles"]:
        raise ValueError(f"A profile named '{cleaned}' already exists.")
    if cleaned == old_name:
        return old_name

    rebuilt: dict[str, dict[str, Any]] = {}
    for name, deck in config["profiles"].items():
        rebuilt[cleaned if name == old_name else name] = deck
    config["profiles"] = rebuilt
    if config["active_profile"] == old_name:
        config["active_profile"] = cleaned
    return cleaned


def delete_profile(config: dict[str, Any], name: str) -> None:
    if name not in config["profiles"]:
        raise KeyError(name)
    if len(config["profiles"]) <= 1:
        raise ValueError("StreamFlow must keep at least one profile.")
    del config["profiles"][name]
    if config["active_profile"] == name:
        config["active_profile"] = next(iter(config["profiles"]))


def export_profile(config: dict[str, Any], profile_name: str, path: Path) -> Path:
    if profile_name not in config["profiles"]:
        raise KeyError(profile_name)
    payload = {
        "streamflow_profile_version": 1,
        "name": profile_name,
        "deck": normalize_deck(config["profiles"][profile_name]),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return path


def import_profile(config: dict[str, Any], path: Path) -> str:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Profile file must contain a JSON object.")

    if "deck" in payload:
        deck = payload.get("deck")
        desired_name = str(payload.get("name", path.stem)).strip() or path.stem
    elif "buttons" in payload or "categories" in payload:
        # Allow importing a legacy StreamFlow deck directly.
        deck = payload
        desired_name = path.stem
    else:
        raise ValueError("This file does not look like a StreamFlow profile.")

    name = unique_profile_name(config, desired_name)
    config["profiles"][name] = normalize_deck(deck)
    config["active_profile"] = name
    return name


def load_config(user_path: Path | None = None, bundled_path: Path | None = None) -> dict[str, Any]:
    user_path = user_path or get_user_config_path()
    for candidate in (user_path, bundled_path):
        if candidate is None or not candidate.exists():
            continue
        try:
            with candidate.open("r", encoding="utf-8") as handle:
                return normalize_config(json.load(handle))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
    return normalize_config(copy.deepcopy(DEFAULT_CONFIG))


def save_config(config: dict[str, Any], path: Path | None = None) -> Path:
    path = path or get_user_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_config(config)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(normalized, handle, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
    return path
