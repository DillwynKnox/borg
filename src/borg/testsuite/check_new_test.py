import pytest
import time
import types
from unittest.mock import MagicMock
import borg.repository 

class MockRepoObj:
    class ObjHeader:
        def __init__(self, *args):
            self.meta_size = 0
            self.data_size = 0
            self.meta_hash = b'hash'
            self.data_hash = b'hash'
    obj_header = MagicMock()
    obj_header.size = 8
    obj_header.unpack = MagicMock(return_value=(0, 0, b'hash', b'hash'))

def mock_xxh64(data): return b'hash'

class FakeStore:
    def __init__(self, objects=None):
        self.objects = objects or {}
        self.deleted = []
        self.stored = {}

    def list(self, prefix):
        return [types.SimpleNamespace(name=k.split("/", 1)[1]) 
                for k in sorted(self.objects.keys())]

    def load(self, key):
        if key not in self.objects:
            from borg.repository import StoreObjectNotFound
            raise StoreObjectNotFound
        return self.objects[key]

    def delete(self, key):
        self.deleted.append(key)
        self.objects.pop(key, None)

    def store(self, key, value):
        self.stored[key] = value



def test_check_repair_deletes_corrupt_object(caplog, monkeypatch):
    monkeypatch.setattr(borg.repository, "RepoObj", MockRepoObj)
    monkeypatch.setattr(borg.repository, "xxh64", mock_xxh64)
    mock_logger = MagicMock()
    monkeypatch.setattr(borg.repository, "logger", mock_logger)
    
    good_id = "0" * 64 
    store = FakeStore(objects={f"data/{good_id}": b"fail"})
    
    repo = MagicMock(spec=borg.repository.Repository)
    repo.store = store
    repo.check = borg.repository.Repository.check.__get__(repo, borg.repository.Repository)
    repo._lock_refresh = MagicMock()

    with caplog.at_level("INFO"):
        ok = repo.check(repair=True, max_duration=0)

    assert ok is True
    assert f"data/{good_id}" in store.deleted
    mock_logger.error.assert_any_call(f"Repo object {good_id} is corrupted: too small.")


def test_check_stops_after_timeout(monkeypatch):
    monkeypatch.setattr(borg.repository, "RepoObj", MockRepoObj)
    monkeypatch.setattr(borg.repository, "xxh64", mock_xxh64)
    
    objects = {f"data/{str(i).zfill(64)}": b"valid_data_hdr" for i in range(10)}
    store = FakeStore(objects=objects)
    
    repo = MagicMock(spec=borg.repository.Repository)
    repo.store = store
    repo.check = borg.repository.Repository.check.__get__(repo, borg.repository.Repository)
    repo._lock_refresh = MagicMock()

    with monkeypatch.context() as m:
        m.setattr(time, "time", MagicMock(side_effect=[100.0, 200.0, 200.0, 200.0, 200.0]))
        repo.check(repair=False, max_duration=0.1)


def test_check_repair_deletes_invalid_hash(monkeypatch):
    monkeypatch.setattr(borg.repository, "RepoObj", MockRepoObj)
    monkeypatch.setattr(borg.repository, "xxh64", lambda x: b'definitely_not_the_mock_hash')
    mock_logger = MagicMock()
    monkeypatch.setattr(borg.repository, "logger", mock_logger)
    
    obj_id = "1" * 64
    store = FakeStore(objects={f"data/{obj_id}": b"1234567890"})
    
    repo = MagicMock(spec=borg.repository.Repository)
    repo.store = store
    repo.check = borg.repository.Repository.check.__get__(repo, borg.repository.Repository)
    repo._lock_refresh = MagicMock()

    repo.check(repair=True, max_duration=0)

    assert f"data/{obj_id}" in store.deleted
    error_msgs = [call.args[0] for call in mock_logger.error.call_args_list]
    assert any("reloading did not help, deleting it!" in msg for msg in error_msgs)

def test_check_empty_repository(monkeypatch):
    monkeypatch.setattr(borg.repository, "RepoObj", MockRepoObj)
    store = FakeStore(objects={}) 
    
    repo = MagicMock(spec=borg.repository.Repository)
    repo.store = store
    repo.check = borg.repository.Repository.check.__get__(repo, borg.repository.Repository)
    repo._lock_refresh = MagicMock()

    ok = repo.check(repair=True)

    assert ok is True
   
    deleted_data = [k for k in store.deleted if k.startswith('data/')]
    assert len(deleted_data) == 0
