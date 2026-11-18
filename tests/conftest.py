import pytest
from fastapi.testclient import TestClient

from app.core.config import PROJECT_ROOT, Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        _env_file=None,
        db_path=tmp_path / "test.sqlite",
        config_dir=PROJECT_ROOT / "config",
        web_dir=PROJECT_ROOT / "web",
        collectors_enabled=False,
    )


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c
