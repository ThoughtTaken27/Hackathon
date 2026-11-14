"""Regression tests for the code-review findings (Sat Nov 14): restart keeps the day, the parent's buttons can't be
pressed by another web page, malformed input gets a 400, a tiny file holding hours of silence can't exhaust memory."""
import io
import json
import os
import time

import numpy as np
import pytest
import soundfile as sf

os.environ.setdefault("HF_HUB_OFFLINE", "1")


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    from fastapi.testclient import TestClient
    import app as kettle_app
    kettle_app.TIMELINE = tmp_path_factory.mktemp("timeline")
    with TestClient(kettle_app.app) as c:
        yield c, kettle_app


def test_persisted_windows_come_back_after_a_restart(client):
    c, kettle_app = client
    from kettle import live
    ev = {"t": time.time(), "start": time.time() - 2, "end": time.time(), "label": "cooking", "conf": 0.9,
          "probs": {"cooking": 0.9}, "sounds": [], "kind": "window10"}
    kettle_app.persist({**ev, "kind": "window"})
    kettle_app.persist({"kind": "log", **live.consent(live.new_state(), time.time() - 5)})
    s = kettle_app.restore()
    assert len(s["events"]) == 1 and s["events"][0]["label"] == "cooking" and s["consent"]


def test_cross_site_page_cannot_press_the_parents_buttons(client):
    c, _ = client
    r = c.post("/api/consent", headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    r = c.post("/api/resume", headers={"Host": "attacker.example"})
    assert r.status_code == 403


def test_malformed_bodies_get_400_not_500(client):
    c, _ = client
    for path, body in (("/api/pause", "[1]"), ("/api/mic", "5"), ("/api/rules", '{"rules": ["x"]}'), ("/api/rules", "null")):
        r = c.post(path, content=body, headers={"Content-Type": "application/json"})
        assert r.status_code == 400, (path, body, r.status_code)


def test_hours_of_silence_in_a_small_file_are_read_only_to_60_s(client):
    c, _ = client
    buf = io.BytesIO()
    sf.write(buf, np.zeros(16000 * 3600, dtype=np.int16), 16000, format="FLAC")   # 1 hour, a few hundred KB
    r = c.post("/api/try", content=buf.getvalue(), headers={"X-Filename": "%E5%BD%95%E9%9F%B3.flac"}).json()
    assert r["status"] == "ok" and r["cut"] and len(r["windows"]) == 6 and r["file"] == "录音.flac"


def test_odd_length_audio_frame_is_ignored_not_fatal():
    from kettle import live
    s, st = live.new_state(), live.new_stream()
    live.consent(s, 0)
    assert live.feed(s, st, b"\x01\x02\x03", 1, None, None) == []


def test_a_1am_snack_does_not_satisfy_a_10am_kitchen_check():
    from kettle import rules, timeline
    from tests.helpers import run_of
    H = 3600
    ev = run_of(1 * H, "eating", 3, dur=300) + run_of(6 * H, "absence", 24, dur=600)
    b = timeline.blocks(ev, 0.5, now=11 * H, listening_now=True, listening_from=1 * H)
    r = rules.evaluate([{"id": "r1", "type": "kitchen_by", "time": "10:00"}], b, 11 * H, 0.0, 0)[0]
    assert r["state"] == "missed"
