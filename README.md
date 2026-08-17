<h1 align="center">
  <img alt="StreamFlow logo" src="/src/icons/logo.png" width="260px"/><br/><br/>
</h1>

# StreamFlow

StreamFlow is a local-first virtual stream deck for Windows, macOS, and Linux. It gives you a customizable desktop button grid for opening websites, launching applications, controlling system audio, and running local commands without requiring a cloud backend or a paid API.

<div style="position: relative; width: max-content;">
  <img src="/src/icons/demo1.png" alt="StreamFlow demo" style="width: 500px;">
  <img src="/src/icons/demo2.png" alt="StreamFlow gallery" style="position: absolute; bottom: -1px; right: -7px; width: 350px;">
</div>

## What works

- Custom categories and button layouts.
- Add, edit, hide, delete, and reorder buttons from the UI.
- Right-click any deck button to edit or delete it.
- Persistent per-user configuration stored outside the repository.
- Open websites in the default browser.
- Launch applications and commands without invoking a shell by default.
- Explicit `shell:` actions when shell syntax is actually needed.
- System mute and volume controls on Windows, macOS, and common Linux audio stacks.
- Optional custom icons.
- Headless unit tests that can run locally or in Docker.

## Install locally

```bash
git clone https://github.com/mergemaven11/streamflow.git
cd streamflow
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Install and launch:

```bash
python -m pip install -r requirements.txt
python src/main.py
```

### Linux audio note

StreamFlow uses the first audio tool it finds: `wpctl` (PipeWire), `pactl` (PulseAudio), or `amixer` (ALSA). Install one of those through your Linux distribution if volume buttons report that no supported audio tool exists.

## Button actions

The UI builds these commands for you:

| Action | Stored command |
| --- | --- |
| Open website | `url:https://example.com` |
| Launch application | `app:/path/to/app` |
| Run command | `cmd:python --version` |
| Run shell expression | `shell:echo hello > output.txt` |
| Mute/unmute | `mute` |
| Volume up | `volume_up` |
| Volume down | `volume_down` |

Use `shell:` only for commands that need shell features such as pipes, redirection, or environment expansion. Normal `app:` and `cmd:` actions launch the executable directly.

## Configuration

Edits are saved to `~/.streamflow/config.json`. Set `STREAMFLOW_CONFIG` to override that path for portable setups or testing.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Or build the test container locally:

```bash
docker compose run --rm test
```

The Docker configuration is intentionally for validation. StreamFlow is a native Qt desktop GUI, so exposing a fake HTTP port from a container is not useful.

## Cost

StreamFlow itself does not need GitHub Codespaces, GitHub Copilot, paid GitHub Actions minutes, a hosted AI model, or any paid API. You can develop, test, and run it entirely on your own machine.
