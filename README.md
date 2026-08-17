<p align="center">
  <img src="./src/icons/logo.png" alt="StreamFlow logo" width="260">
</p>

<h1 align="center">StreamFlow</h1>

<p align="center">
  A modern, local-first virtual control deck for Windows, macOS, and Linux.
</p>

StreamFlow turns your desktop into a customizable action deck for launching apps, opening websites, controlling system audio, driving OBS Studio, and running local commands. It is designed to run entirely on your own machine: no cloud backend, paid API, Codespaces, Copilot, or hosted AI service is required.

## Modern interface

The current StreamFlow UI uses a dark, card-based desktop design with:

- A branded top bar with quick profile switching.
- A dedicated category sidebar.
- Large action cards designed for quick clicking.
- Active-deck and action-count context.
- Polished empty states, forms, menus, and dialogs.
- A consistent violet-accent visual system.
- Responsive spacing for larger desktop windows.

The original prototype screenshots have been removed from this README because the application UI has since been substantially redesigned. Fresh screenshots can be added after the current Windows build is visually smoke-tested.

## Features

### Decks and profiles

- Multiple profiles for separate streaming, work, gaming, support, or personal decks.
- Create, duplicate, rename, delete, and switch profiles.
- Import and export individual profiles as portable JSON files.
- Custom categories and button layouts.
- Add, edit, hide, delete, and reorder actions from the UI.
- Right-click actions to edit or delete them quickly.
- Optional custom button icons.

### Desktop actions

- Open websites in the default browser.
- Launch applications, including executable paths containing spaces.
- Run commands without invoking a shell by default.
- Use explicit `shell:` actions when pipes, redirects, or shell expansion are actually needed.
- Toggle system mute and adjust system volume.
- Windows, macOS, and common Linux audio implementations.

### OBS Studio

StreamFlow includes local OBS WebSocket 5.x control for:

- Switching scenes.
- Toggling an input such as `Mic/Aux` mute.
- Starting and stopping recording.
- Starting and stopping streaming.
- Password-authenticated OBS WebSocket connections.
- Testing the OBS connection directly from StreamFlow settings.

### Local-first configuration

- Configuration is stored in `~/.streamflow/config.json` by default.
- Existing single-deck StreamFlow configs automatically migrate into a `Default` profile.
- `STREAMFLOW_CONFIG` can override the configuration path for portable or test setups.
- OBS credentials remain in the local StreamFlow configuration and are not sent to a cloud service.

## Quick start

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/mergemaven11/streamflow.git
cd streamflow
python -m venv .venv
```

Activate it:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Install dependencies and launch StreamFlow:

```bash
python -m pip install -r requirements.txt
python src/main.py
```

## OBS Studio setup

OBS Studio 28 and newer include obs-websocket by default.

1. Open OBS Studio.
2. Open the WebSocket server settings from the **Tools** menu.
3. Enable the WebSocket server.
4. Keep authentication enabled and copy the password.
5. In StreamFlow, open **OBS connection**.
6. Enter the host, port, and password. Typical local settings are:
   - Host: `127.0.0.1`
   - Port: `4455`
7. Select **Test Connection**.

You can then create actions such as:

- **OBS: Switch scene** — use the exact OBS scene name.
- **OBS: Toggle input mute** — use the exact input name, such as `Mic/Aux`.
- **OBS: Start / stop recording**.
- **OBS: Start / stop streaming**.

## Profiles

Open **Profiles** from the StreamFlow sidebar to maintain separate decks.

- **New** creates a blank deck.
- **Duplicate** copies an existing deck.
- **Rename** changes a profile name.
- **Delete** removes a profile while ensuring at least one remains.
- **Import Profile** loads a JSON deck.
- **Export Profile** saves a portable `.streamflow.json` file.

## Action format

The UI creates the stored action strings automatically:

| Action | Stored command |
| --- | --- |
| Open website | `url:https://example.com` |
| Launch application | `app:/path/to/app` |
| Run command | `cmd:python --version` |
| Run shell expression | `shell:echo hello > output.txt` |
| System mute/unmute | `mute` |
| System volume up | `volume_up` |
| System volume down | `volume_down` |
| OBS scene switch | `obs_scene:Gaming` |
| OBS input mute toggle | `obs_mute:Mic/Aux` |
| OBS recording toggle | `obs_record_toggle` |
| OBS streaming toggle | `obs_stream_toggle` |

Use `shell:` only for commands that genuinely require shell features. Normal `app:` and `cmd:` actions launch directly without a shell.

## Linux audio

On Linux, StreamFlow uses the first supported audio tool it finds:

- `wpctl` for PipeWire.
- `pactl` for PulseAudio.
- `amixer` for ALSA.

Install one of those through your Linux distribution if system audio actions report that no supported tool is available.

## Tests

Install development dependencies and run the local suite:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Or run the validation container:

```bash
docker compose run --rm test
```

The current non-UI logic suite has passed 18 tests, and the modern Qt UI modules pass Python syntax compilation. A local interactive GUI smoke test is still recommended because the automated development environment used for this refactor could not launch PySide6 interactively.

The Docker configuration is intentionally for headless validation. StreamFlow itself is a native Qt desktop application rather than a web service.

## Cost and hosting

StreamFlow does not require:

- GitHub Codespaces.
- GitHub Copilot.
- Paid GitHub Actions minutes.
- A hosted AI model.
- A cloud database or backend.
- A paid API.

Development, testing, configuration, OBS control, and normal use can all happen locally on your own computer.
