from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path
from typing import Any

APP_DIR_NAME = ".streamflow"
CONFIG_FILE_NAME = "config.json"
DEFAULT_CATEGORIES = ["Applications", "Audio", "Video", "Messages", "More"]
DEFAULT_CONFIG: dict[str, Any] = {
    "categories": DEFAULT_CATEGORIES,
    "buttons": [
        {"label": "Open Browser", "command": "url:https://www.google.com", "icon": "", "category": "Applications", "enabled": True},
        {"label": "Mute Audio", "command": "mute", "icon": "", "category": "Audio", "enabled": True},
        {"label": "Volume +", "command": "volume_up", "icon": "", "category": "Audio", "enabled": True},
        {"label": "Volume -", "command": "volume_down", "icon": "", "category": "Audio", "enabled": True},
    ],
}


def get_user_config_path() -> Path:
    override = os.getenv("STREAMFLOW_CONFIG")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / APP_DIR_NAME / CONFIG_FILE_NAME


def normalize_config(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}
    raw_categories = raw.get("categories", [])
    categories: list[str] = []
    if isinstance(raw_categories, list):
        for item in raw_categories:
            category = str(item).strip()
            if category and category not in categories:
                categories.append(category)
    buttons: list[dict[str, Any]] = []
    raw_buttons = raw.get("buttons", [])
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
            buttons.append({"label": label, "command": command, "icon": icon, "category": category, "enabled": enabled})
    if not categories:
        categories = list(DEFAULT_CATEGORIES)
    return {"categories": categories, "buttons": buttons}


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
