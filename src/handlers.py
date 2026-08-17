"""Cross-platform action handlers used by StreamFlow buttons."""
from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ActionResult:
    success: bool
    message: str


def _split_command(command: str) -> list[str]:
    parts = shlex.split(command, posix=sys.platform != "win32")
    if sys.platform == "win32":
        cleaned = []
        for part in parts:
            if len(part) >= 2 and part[0] == part[-1] and part[0] in {"\"", "'"}:
                part = part[1:-1]
            cleaned.append(part)
        return cleaned
    return parts


def _spawn(command: str, *, shell: bool = False) -> None:
    if shell:
        subprocess.Popen(command, shell=True)
        return
    parts = _split_command(command)
    if not parts:
        raise ValueError("Command is empty")
    subprocess.Popen(parts)


def _run(args: Sequence[str]) -> None:
    subprocess.run(list(args), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def execute_command(command: str) -> ActionResult:
    command = (command or "").strip()
    if not command:
        return ActionResult(False, "No action is configured for this button.")
    try:
        if command == "chrome":
            webbrowser.open("https://www.google.com")
            return ActionResult(True, "Opened the default browser.")
        if command == "mute":
            mute_audio()
            return ActionResult(True, "Toggled system mute.")
        if command == "volume_up":
            volume_up()
            return ActionResult(True, "Raised system volume.")
        if command == "volume_down":
            volume_down()
            return ActionResult(True, "Lowered system volume.")
        if command.startswith("url:"):
            url = command[4:].strip()
            if not url:
                raise ValueError("URL is empty")
            opened = webbrowser.open(url)
            if opened is False:
                raise RuntimeError("The system browser did not accept the URL")
            return ActionResult(True, f"Opened {url}")
        if command.startswith("app:"):
            value = command[4:].strip()
            _spawn(value)
            return ActionResult(True, f"Launched {value}")
        if command.startswith("cmd:"):
            value = command[4:].strip()
            _spawn(value)
            return ActionResult(True, f"Ran {value}")
        if command.startswith("shell:"):
            value = command[6:].strip()
            if not value:
                raise ValueError("Shell command is empty")
            _spawn(value, shell=True)
            return ActionResult(True, "Started shell command.")
        _spawn(command)
        return ActionResult(True, f"Ran {command}")
    except Exception as exc:
        return ActionResult(False, f"Action failed: {exc}")


def _windows_endpoint_volume():
    try:
        from comtypes import CLSCTX_ALL
        from ctypes import POINTER, cast
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    except ImportError as exc:
        raise RuntimeError("Windows audio support requires pycaw/comtypes. Reinstall requirements.txt.") from exc
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def _mac_volume(direction: int) -> None:
    delta = 5 if direction > 0 else -5
    script = (
        "set currentVolume to output volume of (get volume settings)\n"
        f"set newVolume to currentVolume + ({delta})\n"
        "if newVolume > 100 then set newVolume to 100\n"
        "if newVolume < 0 then set newVolume to 0\n"
        "set volume output volume newVolume"
    )
    _run(["osascript", "-e", script])


def _mac_toggle_mute() -> None:
    script = "set currentMuted to output muted of (get volume settings)\nset volume output muted (not currentMuted)"
    _run(["osascript", "-e", script])


def _linux_audio_tool() -> str:
    if shutil.which("wpctl"):
        return "wpctl"
    if shutil.which("pactl"):
        return "pactl"
    if shutil.which("amixer"):
        return "amixer"
    raise RuntimeError("No supported Linux audio tool found (wpctl, pactl, or amixer).")


def _linux_volume(direction: int) -> None:
    tool = _linux_audio_tool()
    if tool == "wpctl":
        _run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%+" if direction > 0 else "5%-"])
    elif tool == "pactl":
        _run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%" if direction > 0 else "-5%"])
    else:
        _run(["amixer", "-q", "sset", "Master", "5%+" if direction > 0 else "5%-"])


def _linux_toggle_mute() -> None:
    tool = _linux_audio_tool()
    if tool == "wpctl":
        _run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
    elif tool == "pactl":
        _run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])
    else:
        _run(["amixer", "-q", "sset", "Master", "toggle"])


def volume_up() -> None:
    if sys.platform == "win32":
        volume = _windows_endpoint_volume()
        current = volume.GetMasterVolumeLevelScalar()
        volume.SetMasterVolumeLevelScalar(min(current + 0.05, 1.0), None)
    elif sys.platform == "darwin":
        _mac_volume(1)
    else:
        _linux_volume(1)


def volume_down() -> None:
    if sys.platform == "win32":
        volume = _windows_endpoint_volume()
        current = volume.GetMasterVolumeLevelScalar()
        volume.SetMasterVolumeLevelScalar(max(current - 0.05, 0.0), None)
    elif sys.platform == "darwin":
        _mac_volume(-1)
    else:
        _linux_volume(-1)


def mute_audio() -> None:
    if sys.platform == "win32":
        volume = _windows_endpoint_volume()
        volume.SetMute(not bool(volume.GetMute()), None)
    elif sys.platform == "darwin":
        _mac_toggle_mute()
    else:
        _linux_toggle_mute()
