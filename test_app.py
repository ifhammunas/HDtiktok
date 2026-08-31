from main import app, fetch_tiktok_video


def test_homepage():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    page_html = response.get_data(as_text=True).lower()
    assert "tiktok" in page_html


def test_fetch_tiktok_video_prefers_hd_quality(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_post(self, url, data=None, timeout=None):
        payload = {
            "code": 0,
            "data": {
                "play": "https://example.com/normal.mp4",
                "hdplay": "https://example.com/hd.mp4"
            }
        }
        return FakeResponse(payload)

    monkeypatch.setattr("requests.Session.post", fake_post)

    result = fetch_tiktok_video(
        "https://www.tiktok.com/@user/video/1234567890",
        quality="hd",
    )

    assert result == "https://example.com/hd.mp4"


def test_fetch_tiktok_video_handles_nested_api_payload(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_post(self, url, data=None, timeout=None):
        payload = {
            "code": 0,
            "data": {
                "item_info": {
                    "item_struct": {
                        "video": {
                            "play_addr": {
                                "url_list": [
                                    "https://example.com/hd.mp4"
                                ]
                            }
                        }
                    }
                }
            }
        }
        return FakeResponse(payload)

    monkeypatch.setattr("requests.Session.post", fake_post)

    result = fetch_tiktok_video(
        "https://www.tiktok.com/@user/video/1234567890",
        quality="hd",
    )

    assert result == "https://example.com/hd.mp4"
