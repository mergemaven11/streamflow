import json

from src import obs_client


class FakeSocket:
    def __init__(self, messages):
        self.messages = [json.dumps(message) for message in messages]
        self.sent = []
        self.closed = False

    def recv(self):
        return self.messages.pop(0)

    def send(self, payload):
        self.sent.append(json.loads(payload))

    def close(self):
        self.closed = True


def test_authentication_string_is_deterministic():
    result = obs_client.create_authentication_string(
        "supersecretpassword",
        "lM1GncleQOaCu9lT1yeUZhFYnqhsLLP1G5lAGo3ixaI=",
        "+IxH4CnCiqpX1rM9scsNynZzbOe4KhDeYcTNS3PDaeY=",
    )
    assert result == "1Ct943GAT+6YQUUX47Ia/ncufilbe6+oD6lY+5kaCu4="


def test_connect_identifies_without_auth(monkeypatch):
    fake = FakeSocket(
        [
            {"op": 0, "d": {"rpcVersion": 1}},
            {"op": 2, "d": {"negotiatedRpcVersion": 1}},
        ]
    )
    monkeypatch.setattr(obs_client.websocket, "create_connection", lambda *a, **k: fake)

    client = obs_client.OBSClient().connect()
    assert fake.sent[0]["op"] == 1
    assert fake.sent[0]["d"]["rpcVersion"] == 1
    client.close()
    assert fake.closed is True


def test_request_returns_response_data():
    client = obs_client.OBSClient()
    fake = FakeSocket([])
    client.socket = fake

    request_id_holder = {}

    def send(payload):
        decoded = json.loads(payload)
        fake.sent.append(decoded)
        request_id_holder["id"] = decoded["d"]["requestId"]
        fake.messages.append(
            json.dumps(
                {
                    "op": 7,
                    "d": {
                        "requestType": "GetVersion",
                        "requestId": request_id_holder["id"],
                        "requestStatus": {"result": True, "code": 100},
                        "responseData": {"obsVersion": "32.0.0"},
                    },
                }
            )
        )

    fake.send = send
    response = client.request("GetVersion")
    assert response["obsVersion"] == "32.0.0"


def test_toggle_recording_uses_status_then_start(monkeypatch):
    client = obs_client.OBSClient()
    calls = []

    def request(name, data=None):
        calls.append((name, data))
        if name == "GetRecordStatus":
            return {"outputActive": False}
        return {}

    monkeypatch.setattr(client, "request", request)
    assert client.toggle_recording() is True
    assert calls == [("GetRecordStatus", None), ("StartRecord", None)]


def test_execute_obs_scene_action(monkeypatch):
    calls = []

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def switch_scene(self, scene):
            calls.append(scene)

    monkeypatch.setattr(obs_client, "_client_from_settings", lambda settings: FakeClient())
    result = obs_client.execute_obs_action("obs_scene:Gaming", {})
    assert result.success is True
    assert calls == ["Gaming"]
