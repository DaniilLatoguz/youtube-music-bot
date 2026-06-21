"""Tests for the downloader (yt-dlp is mocked, no network access)."""

from app import downloader


def test_is_url():
    assert downloader._is_url("https://youtu.be/abc")
    assert downloader._is_url("http://example.com")
    assert not downloader._is_url("muse supermassive black hole")
    assert not downloader._is_url("  plain query  ")


class _FakeYDL:
    """Minimal stand-in for yt_dlp.YoutubeDL that records the requested target."""

    last_target = None
    result = {"id": "abc123", "title": "Fake Song", "duration": 100}

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def extract_info(self, target, download=False):
        type(self).last_target = target
        return self.result


def test_get_video_info_passes_url_through(monkeypatch):
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", _FakeYDL)
    info = downloader.get_video_info("https://youtu.be/xyz")
    assert _FakeYDL.last_target == "https://youtu.be/xyz"
    assert info["id"] == "abc123"


def test_get_video_info_prefixes_search_query(monkeypatch):
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", _FakeYDL)
    downloader.get_video_info("muse black hole")
    assert _FakeYDL.last_target == "ytsearch1:muse black hole"


def test_get_video_info_unwraps_search_entries(monkeypatch):
    class _SearchYDL(_FakeYDL):
        result = {"entries": [{"id": "e1", "title": "Entry 1"}, None]}

    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", _SearchYDL)
    info = downloader.get_video_info("something")
    assert info["id"] == "e1"


def test_get_video_info_returns_none_on_error(monkeypatch):
    class _BoomYDL(_FakeYDL):
        def extract_info(self, target, download=False):
            raise RuntimeError("network down")

    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", _BoomYDL)
    assert downloader.get_video_info("x") is None
