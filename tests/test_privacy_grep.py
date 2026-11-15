"""Code audit for the privacy promise: no audio writes, no speech recognition, no browser recording."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# kettle/data.py is the dataset downloader (writes public SINS clips for training); the app never imports it.
RUNTIME = [ROOT / "app.py", *sorted(p for p in (ROOT / "kettle").glob("*.py") if p.name != "data.py")]
STATIC = sorted((ROOT / "static").glob("*.js")) + sorted((ROOT / "static").glob("*.html"))


def text(paths):
    return "\n".join(p.read_text() for p in paths)


def test_no_speech_recognition_anywhere_in_the_product():
    code = text(RUNTIME + STATIC).lower()
    for word in ("whisper", "speech_recognition", "speechrecognition", "webkitspeechrecognition", "transcri", "asr", "vosk", "wav2vec"):
        assert not re.search(rf"\b{word}", code), word


def test_runtime_never_writes_audio():
    code = text(RUNTIME)
    for pat in (r"sf\.write", r"soundfile\.write", r"wave\.open", r"np\.save", r"tempfile", r"pickle\.dump", r"torchaudio\.save"):
        assert not re.search(pat, code), pat
    # the only open-for-write in the runtime is the labels file in app.persist()
    writes = [line.strip() for line in code.splitlines() if re.search(r"open\(.*[\"'][wax]b?\+?[\"']", line)]
    assert writes == ['with open(_day_file(rec.get("t", time.time())), "a") as f:'], writes


def test_browser_never_records_or_stores_audio():
    code = text(STATIC)
    for pat in ("MediaRecorder", "indexedDB", "localStorage", "createObjectURL", "new Blob"):
        assert pat not in code, pat


def test_upload_reads_raw_body_not_multipart():
    code = (ROOT / "app.py").read_text()
    assert "UploadFile" not in code and "await request.body()" in code


def test_app_never_imports_the_dataset_downloader():
    import ast
    for p in RUNTIME:
        tree = ast.parse(p.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "kettle":
                assert "data" not in [a.name for a in node.names], p
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + ([node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
                assert "kettle.data" not in names, p


def test_no_voice_tags_on_the_shown_list():
    """Handover v3.2, 3.5: the family page says Kettle never names voices, so no voice tag may be shown or sent."""
    from kettle import evidence
    for v in ("Speech", "Conversation", "Chatter", "Hubbub, speech noise, speech babble", "Narration, monologue"):
        assert v not in evidence.SHOWN
