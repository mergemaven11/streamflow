from src import handlers


def test_empty_command_is_rejected():
    result = handlers.execute_command("   ")
    assert result.success is False
    assert "No action" in result.message


def test_url_action_uses_default_browser(monkeypatch):
    seen = []
    monkeypatch.setattr(handlers.webbrowser, "open", lambda url: seen.append(url) or True)
    result = handlers.execute_command("url:https://example.com")
    assert result.success is True
    assert seen == ["https://example.com"]


def test_cmd_action_does_not_use_shell(monkeypatch):
    calls = []
    monkeypatch.setattr(handlers, "_spawn", lambda command, shell=False: calls.append((command, shell)))
    result = handlers.execute_command("cmd:python --version")
    assert result.success is True
    assert calls == [("python --version", False)]


def test_shell_action_is_explicit(monkeypatch):
    calls = []
    monkeypatch.setattr(handlers, "_spawn", lambda command, shell=False: calls.append((command, shell)))
    result = handlers.execute_command("shell:echo hello > output.txt")
    assert result.success is True
    assert calls == [("echo hello > output.txt", True)]


def test_legacy_raw_command_stays_shell_free(monkeypatch):
    calls = []
    monkeypatch.setattr(handlers, "_spawn", lambda command, shell=False: calls.append((command, shell)))
    result = handlers.execute_command("python --version")
    assert result.success is True
    assert calls == [("python --version", False)]


def test_volume_action_failure_is_returned_not_raised(monkeypatch):
    def fail():
        raise RuntimeError("audio missing")
    monkeypatch.setattr(handlers, "volume_up", fail)
    result = handlers.execute_command("volume_up")
    assert result.success is False
    assert "audio missing" in result.message
