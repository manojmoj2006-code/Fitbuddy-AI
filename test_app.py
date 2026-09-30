"""Tests run without calling Gemini: the AI functions are replaced with fakes."""
import os
import tempfile

# Must be set before the app is imported.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["GEMINI_API_KEY"] = "test-key"

import pytest
from fastapi.testclient import TestClient

from app import database, routes
from app.gemini_client import GeminiError
from app.main import app

FORM = {"username": "Asha", "user_id": "asha01", "age": "28", "weight": "62.5",
        "goal": "weight loss", "intensity": "medium"}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(routes, "generate_workout_gemini", lambda *a, **k: "Day 1 - Cardio\n- Jog 20 min")
    monkeypatch.setattr(routes, "generate_nutrition_tip_with_flash", lambda *a, **k: "Eat more protein.")
    monkeypatch.setattr(routes, "update_workout_plan", lambda *a, **k: "Day 1 - Cardio\n- Bike 30 min (updated)")
    with TestClient(app) as c:
        yield c


def test_home_and_health(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}


def test_generate_workout_saves_user_and_plan(client):
    r = client.post("/generate-workout", data=FORM)
    assert r.status_code == 200
    assert "Jog 20 min" in r.text and "Eat more protein." in r.text
    assert database.get_user("asha01")["goal"] == "weight loss"
    assert "Jog 20 min" in database.get_original_plan("asha01")


def test_invalid_input_rejected(client):
    r = client.post("/generate-workout", data={**FORM, "age": "5"})
    assert r.status_code == 422
    assert "Please check your input" in r.text


def test_feedback_updates_plan_and_keeps_original(client):
    client.post("/generate-workout", data={**FORM, "user_id": "fb01"})
    r = client.post("/submit-feedback", data={"user_id": "fb01", "feedback": "more cardio"})
    assert r.status_code == 200
    assert "Bike 30 min (updated)" in r.text
    plan = database.get_plan("fb01")
    assert "Jog 20 min" in plan["original_plan"]
    assert "updated" in plan["updated_plan"]
    assert plan["feedback"] == "more cardio"


def test_feedback_unknown_user(client):
    r = client.post("/submit-feedback", data={"user_id": "nobody", "feedback": "more cardio"})
    assert r.status_code == 404


def test_admin_view_and_delete(client):
    client.post("/generate-workout", data={**FORM, "user_id": "adm01", "username": "Zed"})
    page = client.get("/view-all-users")
    assert page.status_code == 200 and "adm01" in page.text and "Zed" in page.text
    r = client.post("/delete-user/adm01", follow_redirects=False)
    assert r.status_code == 303
    assert database.get_user("adm01") is None


def test_gemini_failure_is_shown_not_crashed(client, monkeypatch):
    def boom(*a, **k):
        raise GeminiError("Gemini request failed: quota")
    monkeypatch.setattr(routes, "generate_workout_gemini", boom)
    r = client.post("/generate-workout", data={**FORM, "user_id": "err01"})
    assert r.status_code == 502
    assert "quota" in r.text
    assert database.get_user("err01") is None
