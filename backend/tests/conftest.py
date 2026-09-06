import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
for import_path in (ROOT, ROOT / "backend"):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))


@pytest.fixture()
def client(tmp_path: Path):
    os.environ["TR_PUBAGENT_DB"] = str(tmp_path / "test.db")
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
