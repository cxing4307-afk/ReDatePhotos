from datetime import datetime

from conftest import make_jpeg
from redatephotos.web import create_app


def test_home_page_explains_the_preview_step():
    client = create_app().test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"ReDatePhotos" in response.data
    assert b"Nothing is renamed until you review the preview" in response.data


def test_web_workflow_scans_applies_and_undoes(tmp_path):
    make_jpeg(tmp_path / "from-camera.jpg", captured_at=datetime(2024, 3, 2, 1, 2, 3))
    client = create_app().test_client()

    preview = client.post("/api/scan", json={"directory": str(tmp_path)})
    assert preview.status_code == 200
    assert preview.get_json()["items"][0]["destination"] == "2024-03-02_01-02-03.jpg"

    applied = client.post("/api/apply", json={"directory": str(tmp_path)})
    assert applied.get_json() == {"renamed": 1}
    assert (tmp_path / "2024-03-02_01-02-03.jpg").exists()

    after_apply = client.post("/api/scan", json={"directory": str(tmp_path)}).get_json()
    assert after_apply["items"] == []
    assert after_apply["can_undo"] is True

    undone = client.post("/api/undo", json={"directory": str(tmp_path)})
    assert undone.get_json() == {"restored": 1}
    assert (tmp_path / "from-camera.jpg").exists()
