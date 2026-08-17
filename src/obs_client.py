"""Small synchronous client for the OBS WebSocket 5.x protocol."""
from __future__ import annotations

import base64
import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any

import websocket


@dataclass(frozen=True)
class ActionResult:
    success: bool
    message: str


class OBSError(RuntimeError):
    """Raised when OBS rejects a connection or request."""


def create_authentication_string(password: str, salt: str, challenge: str) -> str:
    secret_hash = hashlib.sha256(f"{password}{salt}".encode("utf-8")).digest()
    secret = base64.b64encode(secret_hash).decode("utf-8")
    auth_hash = hashlib.sha256(f"{secret}{challenge}".encode("utf-8")).digest()
    return base64.b64encode(auth_hash).decode("utf-8")


class OBSClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 4455, password: str = "", timeout: float = 3.0):
        self.host = host.strip() or "127.0.0.1"
        self.port = int(port)
        self.password = password
        self.timeout = timeout
        self.socket = None

    @property
    def url(self) -> str:
        return f"ws://{self.host}:{self.port}"

    def _receive(self) -> dict[str, Any]:
        if self.socket is None:
            raise OBSError("OBS WebSocket is not connected.")
        raw = self.socket.recv()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        try:
            message = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise OBSError("OBS sent an invalid WebSocket message.") from exc
        if not isinstance(message, dict):
            raise OBSError("OBS sent an unexpected WebSocket message.")
        return message

    def connect(self) -> "OBSClient":
        try:
            self.socket = websocket.create_connection(self.url, timeout=self.timeout)
            hello = self._receive()
            if hello.get("op") != 0:
                raise OBSError("OBS did not send the expected Hello message.")

            hello_data = hello.get("d") or {}
            identify_data: dict[str, Any] = {"rpcVersion": 1, "eventSubscriptions": 0}
            authentication = hello_data.get("authentication")
            if isinstance(authentication, dict):
                salt = str(authentication.get("salt", ""))
                challenge = str(authentication.get("challenge", ""))
                if not salt or not challenge:
                    raise OBSError("OBS authentication challenge was incomplete.")
                identify_data["authentication"] = create_authentication_string(
                    self.password, salt, challenge
                )

            self.socket.send(json.dumps({"op": 1, "d": identify_data}))
            identified = self._receive()
            if identified.get("op") != 2:
                raise OBSError("OBS WebSocket authentication or identification failed.")
            return self
        except OBSError:
            self.close()
            raise
        except Exception as exc:
            self.close()
            raise OBSError(f"Could not connect to OBS at {self.url}: {exc}") from exc

    def close(self) -> None:
        if self.socket is not None:
            try:
                self.socket.close()
            finally:
                self.socket = None

    def __enter__(self) -> "OBSClient":
        return self.connect()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def request(self, request_type: str, request_data: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.socket is None:
            raise OBSError("OBS WebSocket is not connected.")

        request_id = str(uuid.uuid4())
        payload: dict[str, Any] = {
            "op": 6,
            "d": {
                "requestType": request_type,
                "requestId": request_id,
            },
        }
        if request_data:
            payload["d"]["requestData"] = request_data
        self.socket.send(json.dumps(payload))

        while True:
            message = self._receive()
            if message.get("op") != 7:
                continue
            data = message.get("d") or {}
            if data.get("requestId") != request_id:
                continue

            status = data.get("requestStatus") or {}
            if not status.get("result", False):
                comment = status.get("comment") or f"request failed with code {status.get('code', 'unknown')}"
                raise OBSError(f"{request_type}: {comment}")
            response = data.get("responseData")
            return response if isinstance(response, dict) else {}

    def get_version(self) -> dict[str, Any]:
        return self.request("GetVersion")

    def switch_scene(self, scene_name: str) -> None:
        self.request("SetCurrentProgramScene", {"sceneName": scene_name})

    def toggle_input_mute(self, input_name: str) -> None:
        self.request("ToggleInputMute", {"inputName": input_name})

    def toggle_recording(self) -> bool:
        status = self.request("GetRecordStatus")
        active = bool(status.get("outputActive", False))
        self.request("StopRecord" if active else "StartRecord")
        return not active

    def toggle_streaming(self) -> bool:
        status = self.request("GetStreamStatus")
        active = bool(status.get("outputActive", False))
        self.request("StopStream" if active else "StartStream")
        return not active


def _client_from_settings(settings: dict[str, Any]) -> OBSClient:
    return OBSClient(
        host=str(settings.get("host", "127.0.0.1")),
        port=int(settings.get("port", 4455)),
        password=str(settings.get("password", "")),
    )


def test_connection(settings: dict[str, Any]) -> str:
    with _client_from_settings(settings) as client:
        version = client.get_version()
    obs_version = version.get("obsVersion", "unknown")
    websocket_version = version.get("obsWebSocketVersion", "unknown")
    return f"Connected to OBS {obs_version} (WebSocket {websocket_version})."


def execute_obs_action(command: str, settings: dict[str, Any]) -> ActionResult:
    command = (command or "").strip()
    try:
        with _client_from_settings(settings) as client:
            if command.startswith("obs_scene:"):
                scene_name = command[len("obs_scene:"):].strip()
                if not scene_name:
                    raise OBSError("OBS scene name is empty.")
                client.switch_scene(scene_name)
                return ActionResult(True, f"Switched OBS to '{scene_name}'.")

            if command.startswith("obs_mute:"):
                input_name = command[len("obs_mute:"):].strip()
                if not input_name:
                    raise OBSError("OBS input name is empty.")
                client.toggle_input_mute(input_name)
                return ActionResult(True, f"Toggled OBS input '{input_name}'.")

            if command == "obs_record_toggle":
                active = client.toggle_recording()
                return ActionResult(True, "OBS recording started." if active else "OBS recording stopped.")

            if command == "obs_stream_toggle":
                active = client.toggle_streaming()
                return ActionResult(True, "OBS streaming started." if active else "OBS streaming stopped.")

            raise OBSError(f"Unknown OBS action: {command}")
    except Exception as exc:
        return ActionResult(False, f"OBS action failed: {exc}")
