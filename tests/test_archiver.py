import os
import pytest

from hookshot.archiver import Archiver, ArchiveError
from hookshot.models import WebhookRequest
from hookshot.storage import RequestStore


@pytest.fixture
def store():
    return RequestStore(max_size=100)


def make_request(method="POST", path="/hook", body=b'{"x": 1}'):
    return WebhookRequest(
        method=method,
        path=path,
        query_string="",
        headers={"content-type": "application/json"},
        body=body,
    )


def test_archiver_requires_path(store):
    with pytest.raises(ArchiveError):
        Archiver(store, "")


def test_save_writes_file(store, tmp_path):
    archive_file = str(tmp_path / "requests.ndjson")
    store.save(make_request())
    store.save(make_request(method="GET", path="/ping", body=b""))
    archiver = Archiver(store, archive_file)
    count = archiver.save()
    assert count == 2
    assert os.path.exists(archive_file)


def test_save_empty_store(store, tmp_path):
    archive_file = str(tmp_path / "empty.ndjson")
    archiver = Archiver(store, archive_file)
    count = archiver.save()
    assert count == 0
    assert os.path.exists(archive_file)


def test_load_restores_requests(store, tmp_path):
    archive_file = str(tmp_path / "requests.ndjson")
    req = make_request()
    store.save(req)
    archiver = Archiver(store, archive_file)
    archiver.save()

    new_store = RequestStore(max_size=100)
    new_archiver = Archiver(new_store, archive_file)
    loaded = new_archiver.load()
    assert loaded == 1
    restored = new_store.get(req.id)
    assert restored is not None
    assert restored.method == "POST"
    assert restored.path == "/hook"


def test_load_skips_existing(store, tmp_path):
    archive_file = str(tmp_path / "requests.ndjson")
    req = make_request()
    store.save(req)
    archiver = Archiver(store, archive_file)
    archiver.save()
    # Load into same store — req already exists
    loaded = archiver.load()
    assert loaded == 0


def test_load_missing_file_returns_zero(store, tmp_path):
    archive_file = str(tmp_path / "nonexistent.ndjson")
    archiver = Archiver(store, archive_file)
    assert archiver.load() == 0


def test_clear_removes_file(store, tmp_path):
    archive_file = str(tmp_path / "requests.ndjson")
    store.save(make_request())
    archiver = Archiver(store, archive_file)
    archiver.save()
    assert os.path.exists(archive_file)
    archiver.clear()
    assert not os.path.exists(archive_file)


def test_clear_no_file_is_safe(store, tmp_path):
    archive_file = str(tmp_path / "ghost.ndjson")
    archiver = Archiver(store, archive_file)
    archiver.clear()  # should not raise
