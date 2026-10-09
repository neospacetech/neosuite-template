from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from neoexample.app import create_app
from neoexample.settings import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(environment="test", stream_interval_seconds=0)


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client
