import os
import tempfile

import pytest

from project import main


@pytest.fixture
def client():
    app = main.create_app()
    app.debug = True
    return app.test_client()


def test_root(client):
    res = client.get("/")
    # print(dir(res), res.status_code)
    assert res.status_code == 200
    assert b"Do The Thing" in res.data


def test_root(client):
    res = client.get("/")
    # print(dir(res), res.status_code)
    assert res.status_code == 200
    assert b"Do The Thing" in res.data